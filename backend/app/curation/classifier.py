import json

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import Settings
from app.curation.base import CurationError
from app.curation.tags import MAX_TAGS, NOUL_THRESHOLD, TAG_REGISTRY
from app.schemas import DatasetCreate


def tag_questions() -> dict[str, dict]:
    return {
        spec.id: {
            "type": "noul",
            "instructions": f"Should this dataset be tagged {spec.id}?",
            "criteria": {
                "true": spec.meaning,
                "false": f"The dataset is not about {spec.id}",
            },
        }
        for spec in TAG_REGISTRY
    }


class NoulAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    noul: float | None = None
    probability: float | None = None

    def score(self) -> float:
        raw = self.noul if self.noul is not None else self.probability
        return float(raw) if raw is not None else 0.0


class JevResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answers: dict[str, NoulAnswer] | None = None
    result: dict | None = None


def tags_from_answers(
    answers: dict,
    *,
    limit: int = MAX_TAGS,
    threshold: float = NOUL_THRESHOLD,
) -> list[str]:
    scored: list[tuple[str, float]] = []
    for spec in TAG_REGISTRY:
        raw = answers.get(spec.id)
        if isinstance(raw, NoulAnswer):
            score = raw.score()
        else:
            score = NoulAnswer.model_validate(raw or {}).score()
        scored.append((spec.id, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [tag for tag, score in scored if score >= threshold][:limit]


def parse_jev_answers(payload: object) -> dict[str, NoulAnswer]:
    try:
        envelope = JevResponse.model_validate(payload)
    except ValidationError as exc:
        raise CurationError("classifier response was not a Jev object") from exc
    if envelope.answers:
        return envelope.answers
    result = envelope.result or {}
    nested = result.get("answers")
    if isinstance(nested, dict):
        return {key: NoulAnswer.model_validate(value) for key, value in nested.items()}
    deeper = result.get("result")
    if isinstance(deeper, dict) and isinstance(deeper.get("answers"), dict):
        return {key: NoulAnswer.model_validate(value) for key, value in deeper["answers"].items()}
    raise CurationError("classifier response missing answers")


class ClassifierCurator:
    """TypeSafe Jev (or a Jev-compatible Clef model) for closed-set tags."""

    def __init__(self, settings: Settings, http_client=None) -> None:
        self.settings = settings
        self._http_client = http_client

    def classify(self, payload: DatasetCreate, dataset_id: str = "") -> list[str]:
        if not self.settings.llm_ready:
            raise CurationError("Cloudflare Workers AI is not configured")

        body = {
            "model": self.settings.classifier_model,
            "input": {
                "state": {"name": payload.name, "description": payload.description},
                "questions": tag_questions(),
            },
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_provider_api_key}",
            "Content-Type": "application/json",
            "cf-aig-gateway-id": self.settings.cf_ai_gateway_id.strip(),
            "cf-aig-metadata": json.dumps(
                {"dataset_id": dataset_id or "pending", "role": "classifier"}
            ),
        }
        if self.settings.cf_ai_gateway_token.strip():
            headers["cf-aig-authorization"] = (
                f"Bearer {self.settings.cf_ai_gateway_token.strip()}"
            )

        client = self._http_client or httpx.Client(timeout=self.settings.request_timeout_seconds)
        close_client = self._http_client is None
        try:
            response = client.post(self.settings.classifier_run_url, json=body, headers=headers)
            if response.status_code >= 400:
                detail = (getattr(response, "text", None) or "")[:400]
                raise CurationError(f"classifier HTTP {response.status_code} {detail}")
            answers = parse_jev_answers(response.json())
        except CurationError:
            raise
        except Exception as exc:
            raise CurationError(f"classifier failed: {type(exc).__name__}") from exc
        finally:
            if close_client:
                client.close()

        tags = tags_from_answers(answers)
        if not tags:
            raise CurationError("classifier returned no tags above threshold")
        return tags
