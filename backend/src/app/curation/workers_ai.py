import asyncio
import json
import logging
import re
import time
import uuid
from typing import Any

from pydantic import BaseModel, field_validator

from app.curation.base import CurationResult, IncompleteCurationError
from app.curation.prompts import MAX_SUMMARY_WORDS, SUMMARY_INSTRUCTIONS, summary_prompt
from app.curation.tags import ALL_TAGS, MAX_TAGS
from app.logs import describe, log_event
from app.schemas import DatasetCreate

logger = logging.getLogger(__name__)

# A tag is kept when Clef's probability for it is at least this high.
TAG_THRESHOLD = 0.55

# One deadline covers both model calls and any retry, so the user waits at most this long for curation.
DEFAULT_TIMEOUT_SECONDS = 15.0

# Workers AI errors worth one retry: 3007 timeout, 3008 aborted, 3040 out of capacity.
# https://developers.cloudflare.com/workers-ai/platform/errors/
TRANSIENT_ERROR = re.compile(r"\b(?:3007|3008|3040)\b")

# The curation log records this many of Clef's highest scores, including tags under the threshold.
LOGGED_SCORES = 8


class Summary(BaseModel):
    """The JSON object the summary model must return."""

    summary: str

    @field_validator("summary")
    @classmethod
    def at_most_max_words(cls, value: str) -> str:
        if len(value.split()) > MAX_SUMMARY_WORDS:
            raise ValueError(f"summary is longer than {MAX_SUMMARY_WORDS} words")
        return value


class WorkersAiCurator:
    """Two Workers AI calls: Clef picks tags from the closed vocabulary, then a chat model writes the summary.

    Clef is a decision model. It answers one yes/no question per tag with a probability, so tags never leave
    the vocabulary. The summary request uses JSON mode and is validated with Pydantic.

    If Clef fails, curate raises and the dataset is saved without tags. If only the summary fails, it raises
    IncompleteCurationError with Clef's tags. Each call logs one "curation" event with timings, scores, and
    the outcome. Its curation_id is also sent to AI Gateway as metadata, so filtering the gateway logs by
    that id shows the exact prompts and responses behind the event.
    """

    def __init__(
        self,
        ai: Any,
        classifier_model: str,
        summary_model: str,
        gateway_id: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._ai = ai
        self._classifier_model = classifier_model
        self._summary_model = summary_model
        self._gateway_id = gateway_id
        self._timeout_seconds = timeout_seconds

    async def curate(self, dataset: DatasetCreate) -> CurationResult:
        deadline = time.monotonic() + self._timeout_seconds
        event: dict[str, Any] = {
            "curation_id": uuid.uuid4().hex,
            "dataset": dataset.name,
            "classifier_model": self._classifier_model,
            "summary_model": self._summary_model,
            "outcome": "failed",
        }
        try:
            try:
                tags = await self._classify(dataset, deadline, event)
            except Exception as exc:
                event["error"] = describe(exc)
                raise
            try:
                summary = await self._summarise(dataset, tags, deadline, event)
            except Exception as exc:
                event.update(outcome="incomplete", error=describe(exc))
                raise IncompleteCurationError(tags) from exc
            event.update(outcome="ok", summary_words=len(summary.split()))
            return CurationResult(tags=tags, summary=summary)
        finally:
            level = logging.INFO if event["outcome"] == "ok" else logging.WARNING
            log_event(logger, level, "curation", **event)

    async def _classify(self, dataset: DatasetCreate, deadline: float, event: dict[str, Any]) -> list[str]:
        request = {
            "state": {"name": dataset.name, "description": dataset.description},
            "questions": {
                tag.id: {
                    "type": "noul",
                    "instructions": f"Should this dataset be tagged {tag.id}?",
                    "criteria": {"true": tag.meaning, "false": f"The dataset is not about {tag.id}"},
                }
                for tag in ALL_TAGS
            },
        }
        reply = await self._run("classify", self._classifier_model, request, deadline, event)
        scores = scores_from_answers(reply["answers"])
        tags = tags_from_scores(scores)
        event.update(scores=dict(scores[:LOGGED_SCORES]), tags=tags)
        return tags

    async def _summarise(self, dataset: DatasetCreate, tags: list[str], deadline: float, event: dict[str, Any]) -> str:
        request = {
            "messages": [
                {"role": "system", "content": SUMMARY_INSTRUCTIONS},
                {"role": "user", "content": summary_prompt(dataset.name, dataset.description, tags)},
            ],
            "response_format": {"type": "json_schema", "json_schema": Summary.model_json_schema()},
            "temperature": 0,
        }
        reply = await self._run("summary", self._summary_model, request, deadline, event)
        response = reply["response"]
        if isinstance(response, str):  # some models return the JSON object as text
            response = json.loads(response)
        return Summary.model_validate(response).summary

    async def _run(self, step: str, model: str, request: dict[str, Any], deadline: float, event: dict[str, Any]) -> Any:
        """Calls the model within the deadline, retrying once on a transient Workers AI error."""
        options = self._options(step, event["curation_id"])
        started = time.monotonic()
        try:
            try:
                return await self._run_once(model, request, options, deadline)
            except Exception as exc:
                if not TRANSIENT_ERROR.search(str(exc)):
                    raise
                event[f"{step}_retried_after"] = describe(exc)
                return await self._run_once(model, request, options, deadline)
        finally:
            event[f"{step}_ms"] = round((time.monotonic() - started) * 1000)

    async def _run_once(self, model: str, request: dict[str, Any], options: dict[str, Any], deadline: float) -> Any:
        return await asyncio.wait_for(self._ai.run(model, request, options), timeout=deadline - time.monotonic())

    def _options(self, step: str, curation_id: str) -> dict[str, Any]:
        """Routes the call through AI Gateway, which logs each prompt and response with latency and tokens."""
        if not self._gateway_id:
            return {}
        return {"gateway": {"id": self._gateway_id, "metadata": {"curation_id": curation_id, "step": step}}}


def scores_from_answers(answers: dict[str, dict[str, Any]]) -> list[tuple[str, float]]:
    """Clef's probability for each vocabulary tag it answered, highest first."""
    scores = [(tag.id, float(answers[tag.id]["noul"])) for tag in ALL_TAGS if tag.id in answers]
    return sorted(scores, key=lambda item: item[1], reverse=True)


def tags_from_scores(scores: list[tuple[str, float]]) -> list[str]:
    """Keeps the tags at or above TAG_THRESHOLD, at most MAX_TAGS. `scores` must be sorted highest first."""
    return [tag for tag, score in scores if score >= TAG_THRESHOLD][:MAX_TAGS]
