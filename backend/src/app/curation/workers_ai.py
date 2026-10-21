import asyncio
import json
from typing import Any

from pydantic import BaseModel, field_validator

from app.curation.base import CurationResult
from app.curation.prompts import MAX_SUMMARY_WORDS, SUMMARY_INSTRUCTIONS, summary_prompt
from app.curation.tags import ALL_TAGS, MAX_TAGS
from app.schemas import DatasetCreate

# A tag is kept when Clef's probability for it is at least this high.
TAG_THRESHOLD = 0.55

# Each model call gets this long before curation gives up and the dataset is saved as "failed".
DEFAULT_TIMEOUT_SECONDS = 20.0


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
    the vocabulary. The summary request uses JSON mode and is validated with Pydantic. Any failure, including
    a timeout, raises, and DatasetService records the dataset as curation_status "failed".
    """

    def __init__(
        self,
        ai: Any,
        classifier_model: str,
        summary_model: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._ai = ai
        self._classifier_model = classifier_model
        self._summary_model = summary_model
        self._timeout_seconds = timeout_seconds

    async def curate(self, dataset: DatasetCreate) -> CurationResult:
        tags = await self._classify(dataset)  # may be empty; the summary is still worth having
        summary = await self._summarise(dataset, tags)
        return CurationResult(tags=tags, summary=summary)

    async def _classify(self, dataset: DatasetCreate) -> list[str]:
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
        reply = await self._run(self._classifier_model, request)
        return tags_from_answers(reply["answers"])

    async def _summarise(self, dataset: DatasetCreate, tags: list[str]) -> str:
        request = {
            "messages": [
                {"role": "system", "content": SUMMARY_INSTRUCTIONS},
                {"role": "user", "content": summary_prompt(dataset.name, dataset.description, tags)},
            ],
            "response_format": {"type": "json_schema", "json_schema": Summary.model_json_schema()},
            "temperature": 0,
        }
        reply = await self._run(self._summary_model, request)
        response = reply["response"]
        if isinstance(response, str):  # some models return the JSON object as text
            response = json.loads(response)
        return Summary.model_validate(response).summary

    async def _run(self, model: str, request: dict[str, Any]) -> Any:
        return await asyncio.wait_for(self._ai.run(model, request), timeout=self._timeout_seconds)


def tags_from_answers(answers: dict[str, dict[str, Any]]) -> list[str]:
    """Keeps the tags Clef said yes to, highest probability first, at most MAX_TAGS."""
    scored = [(tag.id, float(answers[tag.id]["noul"])) for tag in ALL_TAGS if tag.id in answers]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [tag for tag, score in scored if score >= TAG_THRESHOLD][:MAX_TAGS]
