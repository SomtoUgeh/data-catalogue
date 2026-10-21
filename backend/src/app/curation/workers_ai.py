import json
from typing import Any

from pydantic import BaseModel

from app.curation.base import CurationResult
from app.curation.prompts import SUMMARY_INSTRUCTIONS, summary_prompt
from app.curation.tags import ALL_TAGS, MAX_TAGS
from app.schemas import DatasetCreate

# A tag is kept when Clef's probability for it is at least this high.
TAG_THRESHOLD = 0.55


class Summary(BaseModel):
    summary: str


class WorkersAiCurator:
    """Two Workers AI calls: Clef picks tags from the closed vocabulary, then a chat model writes the summary.

    Clef is a decision model. It answers one yes/no question per tag with a probability, so tags never leave
    the vocabulary. The summary request uses JSON mode and is validated with Pydantic. Any failure raises,
    and DatasetService records the dataset as curation_status "failed".
    """

    def __init__(self, ai: Any, classifier_model: str, summary_model: str) -> None:
        self._ai = ai
        self._classifier_model = classifier_model
        self._summary_model = summary_model

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
        reply = await self._ai.run(self._classifier_model, request)
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
        reply = await self._ai.run(self._summary_model, request)
        response = reply["response"]
        if isinstance(response, str):  # some models return the JSON object as text
            response = json.loads(response)
        return Summary.model_validate(response).summary


def tags_from_answers(answers: dict[str, dict[str, Any]]) -> list[str]:
    """Keeps the tags Clef said yes to, highest probability first, at most MAX_TAGS."""
    scored = [(tag.id, float(answers[tag.id]["noul"])) for tag in ALL_TAGS if tag.id in answers]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [tag for tag, score in scored if score >= TAG_THRESHOLD][:MAX_TAGS]
