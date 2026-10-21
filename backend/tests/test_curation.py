import json

import httpx
import pytest
from pydantic_ai import ModelResponse, TextPart, models
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from app.config import DEFAULT_CLASSIFIER_MODEL, DEFAULT_LLM_MODEL, Settings, get_settings
from app.curation.classifier import ClassifierCurator, tags_from_answers
from app.curation.tags import TAG_REGISTRY
from app.curation.factory import get_curator
from app.curation.hybrid import HybridCurator
from app.curation.llm import LlmCurator
from app.curation.outcome import PLACEHOLDER_SUMMARY, compose_curation
from app.curation.tags import normalize_tags
from app.schemas import CurationResult, DatasetCreate
from app.services.dataset_service import _safe_error

models.ALLOW_MODEL_REQUESTS = False

TRADE = DatasetCreate(
    name="Trade Confirmations",
    owner="Middle Office",
    description=(
        "Daily export of confirmed trades including instrument type, "
        "counterparty, notional value, and settlement date."
    ),
)

VALID_OUTPUT = {
    "tags": ["trading", "finance", "settlements", "daily"],
    "summary": "A daily export of confirmed trades covering counterparties and settlements.",
}

def test_get_curator_is_always_hybrid(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "CF_ACCOUNT_ID",
        "CF_AI_GATEWAY_ID",
        "LLM_PROVIDER_API_KEY",
        "CURATOR",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    curator = get_curator()
    assert isinstance(curator, HybridCurator)
    assert isinstance(curator.classifier, ClassifierCurator)
    assert curator.classifier.settings.llm_model == DEFAULT_LLM_MODEL
    assert curator.classifier.settings.classifier_model == DEFAULT_CLASSIFIER_MODEL


def test_normalize_tags_lowercases_dedupes_and_keeps_acronyms() -> None:
    assert normalize_tags(
        ["Finance", "FINANCE", "PII", "middle", "NOTIONAL_VALUE!", "daily", "weekly", "extra"]
    ) == ["finance", "PII", "middle", "notional_value", "daily"]


def test_curation_result_rejects_short_or_wordy_summaries() -> None:
    with pytest.raises(ValueError):
        CurationResult(tags=["trading", "finance", "daily"], summary="Nope")
    with pytest.raises(ValueError):
        CurationResult(
            tags=["trading", "finance", "daily"],
            summary="A " + "word " * 30,
        )


def _settings() -> Settings:
    return Settings(
        cf_account_id="test-account-id",
        cf_ai_gateway_id="test-gateway",
        llm_provider_api_key="cf-token",
    )


def _function_model(*texts: str) -> FunctionModel:
    remaining = list(texts)

    def reply(_messages, _info) -> ModelResponse:
        content = remaining.pop(0) if remaining else texts[-1]
        return ModelResponse(parts=[TextPart(content)])

    return FunctionModel(reply)


def test_llm_curator_accepts_valid_testmodel_output() -> None:
    curator = LlmCurator(
        _settings(),
        model=TestModel(custom_output_text=json.dumps(VALID_OUTPUT)),
    )
    result = curator.curate(TRADE, dataset_id="4")
    assert result.tags == VALID_OUTPUT["tags"]
    assert result.summary.startswith("A daily export")


def test_llm_curator_retries_invalid_then_valid_function_model() -> None:
    curator = LlmCurator(
        _settings(),
        model=_function_model(
            json.dumps({"tags": ["x"], "summary": "Nope"}),
            json.dumps(VALID_OUTPUT),
        ),
    )
    result = curator.curate(TRADE, dataset_id="4")
    assert result.tags == VALID_OUTPUT["tags"]


def test_safe_error_redacts_bearer_tokens() -> None:
    class FakeError(Exception):
        pass

    message = _safe_error(FakeError("401 Authorization: Bearer super-secret-token"))
    assert "super-secret-token" not in message
    assert "[redacted]" in message
    assert "FakeError" in message


def test_tag_set_does_not_include_trades() -> None:
    assert "trades" not in {spec.id for spec in TAG_REGISTRY}


def test_tags_from_answers_keeps_high_noul_scores() -> None:
    answers = {
        "trading": {"type": "noul", "noul": 0.92},
        "trades": {"type": "noul", "noul": 0.99},
        "finance": {"type": "noul", "noul": 0.81},
        "settlements": {"type": "noul", "noul": 0.77},
        "daily": {"type": "noul", "noul": 0.88},
        "PII": {"type": "noul", "noul": 0.04},
        "HR": {"type": "noul", "noul": 0.01},
    }
    tags = tags_from_answers(answers)
    assert tags == ["trading", "daily", "finance", "settlements"]
    assert "trades" not in tags


def test_tags_from_answers_caps_at_five_highest_scores() -> None:
    answers = {
        "trading": {"noul": 0.99},
        "finance": {"noul": 0.95},
        "settlements": {"noul": 0.9},
        "daily": {"noul": 0.88},
        "transactions": {"noul": 0.8},
        "operations": {"noul": 0.7},
        "HR": {"noul": 0.6},
    }
    tags = tags_from_answers(answers)
    assert tags == ["trading", "finance", "settlements", "daily", "transactions"]
    assert len(tags) == 5


def test_tags_from_answers_omits_scores_below_threshold() -> None:
    answers = {
        "trading": {"noul": 0.2},
        "finance": {"noul": 0.18},
        "daily": {"noul": 0.11},
        "HR": {"noul": 0.02},
    }
    assert tags_from_answers(answers) == []


def test_classifier_curator_maps_mocked_http_response() -> None:
    payload = {
        "result": {
            "answers": {
                "trading": {"noul": 0.9},
                "finance": {"noul": 0.8},
                "settlements": {"noul": 0.7},
                "daily": {"noul": 0.85},
            }
        }
    }

    class FakeClient:
        def post(self, url, json, headers):
            assert url.endswith("/ai/run")
            assert json["model"] == DEFAULT_CLASSIFIER_MODEL
            assert "Authorization" in headers
            assert json["input"]["state"]["name"] == TRADE.name
            return httpx.Response(200, json=payload)

    curator = ClassifierCurator(_settings(), http_client=FakeClient())
    tags = curator.classify(TRADE, dataset_id="4")
    assert set(tags) >= {"trading", "finance", "settlements", "daily"}


def test_compose_curation_is_a_discriminated_union() -> None:
    ok = compose_curation(["trading", "finance", "daily"], "A daily export of confirmed trades.")
    assert ok.status == "ok"
    assert ok.tags == ["trading", "finance", "daily"]

    tags_only = compose_curation(["trading", "finance", "daily"], None)
    assert tags_only.status == "partial"
    assert tags_only.tags == ["trading", "finance", "daily"]
    assert tags_only.summary == PLACEHOLDER_SUMMARY

    summary_only = compose_curation(None, "A daily export of confirmed trades.")
    assert summary_only.status == "partial"
    assert summary_only.tags == []

    failed = compose_curation(None, None)
    assert failed.status == "failed"
    assert failed.tags == []
    assert failed.summary == PLACEHOLDER_SUMMARY


def test_hybrid_uses_classifier_tags_and_llm_summary() -> None:
    class FakeClassifier(ClassifierCurator):
        def classify(self, payload, dataset_id=""):
            return ["trading", "finance", "daily"]

    summarizer = LlmCurator(
        _settings(),
        model=TestModel(
            custom_output_text=json.dumps({"summary": "A daily export of confirmed trades."})
        ),
    )
    curator = HybridCurator(FakeClassifier(_settings()), summarizer)
    result = curator.curate(TRADE)
    assert result.status == "ok"
    assert result.tags == ["trading", "finance", "daily"]
    assert result.summary.startswith("A daily export")


def test_hybrid_keeps_summary_when_classifier_fails() -> None:
    class BoomClassifier(ClassifierCurator):
        def classify(self, payload, dataset_id=""):
            raise RuntimeError("gateway down")

    summarizer = LlmCurator(
        _settings(),
        model=TestModel(custom_output_text=json.dumps({"summary": VALID_OUTPUT["summary"]})),
    )
    result = HybridCurator(BoomClassifier(_settings()), summarizer).curate(TRADE)
    assert result.status == "partial"
    assert result.tags == []
    assert result.summary.startswith("A daily export")


def test_hybrid_keeps_tags_when_summarizer_fails() -> None:
    class FakeClassifier(ClassifierCurator):
        def classify(self, payload, dataset_id=""):
            return ["trading", "finance", "daily"]

    class BoomSummarizer:
        def summarise(self, payload, tags, dataset_id=""):
            raise RuntimeError("llm down")

    result = HybridCurator(FakeClassifier(_settings()), BoomSummarizer()).curate(TRADE)
    assert result.status == "partial"
    assert result.tags == ["trading", "finance", "daily"]
    assert result.summary == PLACEHOLDER_SUMMARY


def test_llm_summarise_accepts_valid_testmodel_output() -> None:
    curator = LlmCurator(
        _settings(),
        model=TestModel(custom_output_text=json.dumps({"summary": VALID_OUTPUT["summary"]})),
    )
    summary = curator.summarise(TRADE, ["trading", "finance", "daily"])
    assert summary.startswith("A daily export")
