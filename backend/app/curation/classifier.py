import json

import httpx

from app.config import Settings
from app.curation.base import CurationError
from app.schemas import DatasetCreate

DEFAULT_CLASSIFIER_MODEL = "typesafe/jev"
NOUL_THRESHOLD = 0.55

# One yes/no question per catalogue tag. Jev is a decision model: it returns
# a probability, not free text, so the closed tag set stays closed.
TAG_CRITERIA: list[tuple[str, str]] = [
    ("finance", "Money, amounts, currencies, P&L, capital, or financial reporting"),
    ("trading", "Trades, instruments, counterparties, confirmations, or trading books"),
    ("settlements", "Settlement dates, clearing, collateral, or post-trade settlement"),
    ("transactions", "Transaction records, payments, or transfers"),
    ("inventory", "Stock levels, SKUs, quantity on hand, or reorder thresholds"),
    ("operations", "Operational processes, warehouse operations, or ops workflows"),
    ("warehouse", "Warehouse locations or stored stock"),
    ("HR", "Employees, departments, roles, or HR records"),
    ("employees", "People who work at the firm, as the data subject"),
    ("customers", "Customers or clients as the data subject"),
    ("products", "Products or SKUs as the data subject"),
    (
        "PII",
        "The description names people-identifying fields such as customer ID, name, or email — not merely a product name",
    ),
    ("daily", "The feed or snapshot is produced daily"),
    ("weekly", "The feed or snapshot is produced weekly"),
    ("monthly", "The feed or snapshot is produced monthly"),
]


def tag_questions() -> dict[str, dict]:
    return {
        tag: {
            "type": "noul",
            "instructions": f"Should this dataset be tagged {tag}?",
            "criteria": {
                "true": meaning,
                "false": f"The dataset is not about {tag}",
            },
        }
        for tag, meaning in TAG_CRITERIA
    }


def tags_from_answers(answers: dict, *, limit: int = 6, threshold: float = NOUL_THRESHOLD) -> list[str]:
    scored: list[tuple[str, float]] = []
    for tag, _meaning in TAG_CRITERIA:
        score = _noul(answers.get(tag))
        scored.append((tag, score))
    scored.sort(key=lambda item: item[1], reverse=True)

    tags = [tag for tag, score in scored if score >= threshold][:limit]
    if len(tags) < 3:
        tags = [tag for tag, _score in scored[:3]]
    return tags


def _noul(answer: object) -> float:
    if not isinstance(answer, dict):
        return 0.0
    raw = answer.get("noul", answer.get("probability", 0.0))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _extract_answers(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise CurationError("classifier response was not an object")
    if isinstance(payload.get("answers"), dict):
        return payload["answers"]
    result = payload.get("result")
    if isinstance(result, dict):
        if isinstance(result.get("answers"), dict):
            return result["answers"]
        nested = result.get("result")
        if isinstance(nested, dict) and isinstance(nested.get("answers"), dict):
            return nested["answers"]
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
            answers = _extract_answers(response.json())
        except CurationError:
            raise
        except Exception as exc:
            raise CurationError(f"classifier failed: {type(exc).__name__}") from exc
        finally:
            if close_client:
                client.close()

        tags = tags_from_answers(answers)
        if len(tags) < 3:
            raise CurationError("classifier returned fewer than 3 tags")
        return tags
