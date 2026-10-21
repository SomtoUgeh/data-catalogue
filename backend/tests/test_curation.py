import json

import httpx
import pytest
from pydantic_ai import ModelResponse, TextPart, models
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from app.config import DEFAULT_CLASSIFIER_MODEL, DEFAULT_LLM_MODEL, Settings, get_settings
from app.curation.classifier import ClassifierCurator, tags_from_answers
from app.curation.factory import get_curator
from app.curation.hybrid import HybridCurator
from app.curation.keyword import KeywordCurator
from app.curation.llm import LlmCurator
from app.curation.tags import normalize_tags
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import CurationResult, DatasetCreate
from app.services.dataset_service import PLACEHOLDER_SUMMARY, PLACEHOLDER_TAGS, _safe_error
from fastapi.testclient import TestClient

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

TRADE_PAYLOAD = {
    "name": TRADE.name,
    "owner": TRADE.owner,
    "description": TRADE.description,
}


def test_keyword_curator_tags_trade_confirmations() -> None:
    result = KeywordCurator().curate(TRADE)
    assert set(result.tags) >= {"trading", "finance", "settlements", "daily"}
    assert result.summary.startswith("A daily export of confirmed trades")
    assert len(result.summary.rstrip(".").split()) <= 25


def test_keyword_curator_detects_pii_and_hr() -> None:
    payload = DatasetCreate(
        name="Employee Directory",
        owner="HR Team",
        description="List of current employees with name, department, role, and office location. Updated weekly.",
    )
    result = KeywordCurator().curate(payload)
    assert "HR" in result.tags
    assert "PII" in result.tags
    assert "weekly" in result.tags
    assert result.summary.startswith("A ")


def test_keyword_curator_does_not_treat_product_name_as_pii() -> None:
    payload = DatasetCreate(
        name="Product Inventory",
        owner="Operations Team",
        description="Snapshot of warehouse stock levels by SKU, including product name and quantity on hand.",
    )
    result = KeywordCurator().curate(payload)
    assert "inventory" in result.tags
    assert "PII" not in result.tags
    assert result.summary.startswith("A ")


def test_get_curator_defaults_to_keyword_without_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "CF_ACCOUNT_ID",
        "CF_AI_GATEWAY_ID",
        "LLM_PROVIDER_API_KEY",
        "CURATOR",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    assert isinstance(get_curator(), KeywordCurator)


def test_get_curator_uses_hybrid_when_gateway_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-account-id")
    monkeypatch.setenv("CF_AI_GATEWAY_ID", "test-gateway")
    monkeypatch.setenv("LLM_PROVIDER_API_KEY", "token")
    monkeypatch.delenv("CURATOR", raising=False)
    get_settings.cache_clear()
    curator = get_curator()
    assert isinstance(curator, HybridCurator)
    assert isinstance(curator.classifier, ClassifierCurator)
    assert curator.classifier.settings.llm_model == DEFAULT_LLM_MODEL
    assert curator.classifier.settings.classifier_model == DEFAULT_CLASSIFIER_MODEL


def test_get_curator_llm_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CF_ACCOUNT_ID", "acc")
    monkeypatch.setenv("CF_AI_GATEWAY_ID", "gw")
    monkeypatch.setenv("LLM_PROVIDER_API_KEY", "token")
    monkeypatch.setenv("CURATOR", "llm")
    get_settings.cache_clear()
    assert isinstance(get_curator(), LlmCurator)


def test_get_curator_classifier_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CF_ACCOUNT_ID", "acc")
    monkeypatch.setenv("CF_AI_GATEWAY_ID", "gw")
    monkeypatch.setenv("LLM_PROVIDER_API_KEY", "token")
    monkeypatch.setenv("CURATOR", "classifier")
    get_settings.cache_clear()
    assert isinstance(get_curator(), ClassifierCurator)


def test_get_curator_mock_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CF_ACCOUNT_ID", "acc")
    monkeypatch.setenv("CF_AI_GATEWAY_ID", "gw")
    monkeypatch.setenv("LLM_PROVIDER_API_KEY", "token")
    monkeypatch.setenv("CURATOR", "mock")
    get_settings.cache_clear()
    assert isinstance(get_curator(), KeywordCurator)


def test_normalize_tags_lowercases_dedupes_and_keeps_acronyms() -> None:
    assert normalize_tags(
        ["Finance", "FINANCE", "PII", "middle", "NOTIONAL_VALUE!", "daily", "weekly", "extra"]
    ) == ["finance", "PII", "middle", "notional_value", "daily", "weekly"]


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


def test_tags_from_answers_keeps_high_noul_scores() -> None:
    answers = {
        "trading": {"type": "noul", "noul": 0.92},
        "finance": {"type": "noul", "noul": 0.81},
        "settlements": {"type": "noul", "noul": 0.77},
        "daily": {"type": "noul", "noul": 0.88},
        "PII": {"type": "noul", "noul": 0.04},
        "HR": {"type": "noul", "noul": 0.01},
    }
    assert tags_from_answers(answers) == ["trading", "daily", "finance", "settlements"]


def test_tags_from_answers_pads_to_three_when_scores_are_low() -> None:
    answers = {
        "trading": {"noul": 0.2},
        "finance": {"noul": 0.18},
        "daily": {"noul": 0.11},
        "HR": {"noul": 0.02},
    }
    assert tags_from_answers(answers) == ["trading", "finance", "daily"]


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
    result = curator.curate(TRADE, dataset_id="4")
    assert set(result.tags) >= {"trading", "finance", "settlements", "daily"}
    assert result.summary.startswith("A ")


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
    assert result.tags == ["trading", "finance", "daily"]
    assert result.summary.startswith("A daily export")


def test_hybrid_falls_back_to_keyword_when_classifier_fails() -> None:
    class BoomClassifier(ClassifierCurator):
        def classify(self, payload, dataset_id=""):
            raise RuntimeError("gateway down")

    curator = HybridCurator(BoomClassifier(_settings()), summarizer=None)
    result = curator.curate(TRADE)
    assert set(result.tags) >= {"trading", "finance", "settlements", "daily"}


def test_llm_summarise_accepts_valid_testmodel_output() -> None:
    curator = LlmCurator(
        _settings(),
        model=TestModel(custom_output_text=json.dumps({"summary": VALID_OUTPUT["summary"]})),
    )
    summary = curator.summarise(TRADE, ["trading", "finance", "daily"])
    assert summary.startswith("A daily export")


def test_llm_failure_falls_back_on_create() -> None:
    curator = LlmCurator(
        _settings(),
        model=_function_model(json.dumps({"tags": ["x"], "summary": "Nope"})),
    )
    client = TestClient(create_app(repository=DatasetRepository(), curator=curator))

    response = client.post("/datasets", json=TRADE_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["tags"] == PLACEHOLDER_TAGS
    assert body["summary"] == PLACEHOLDER_SUMMARY
    assert body["curation_status"] == "failed"
