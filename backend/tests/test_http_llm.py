import json
from types import SimpleNamespace

import httpx
from app.config import Settings, settings_from_env
from app.curation.factory import get_worker_curator
from app.curation.http_llm import HttpLlmCurator, _message_text
from app.curation.hybrid import HybridCurator
from app.curation.outcome import PLACEHOLDER_SUMMARY
from app.curation.summary import parse_summary
from app.schemas import DatasetCreate, SummaryResult

TRADE = DatasetCreate(
    name="Trade Confirmations",
    owner="Middle Office",
    description=(
        "Daily export of confirmed trades including instrument type, "
        "counterparty, notional value, and settlement date."
    ),
)

VALID = "A daily export of confirmed trades covering counterparties and settlements."


def test_parse_summary_accepts_json_object_and_fenced_text() -> None:
    assert parse_summary(json.dumps({"summary": VALID})) == VALID
    fenced = f"```json\n{json.dumps({'summary': VALID})}\n```"
    assert parse_summary(fenced) == VALID


def test_parse_summary_rejects_invalid_sentence() -> None:
    try:
        parse_summary(json.dumps({"summary": "Nope"}))
    except Exception as exc:
        assert exc.__class__.__name__ == "CurationError"
    else:
        raise AssertionError("expected CurationError")


def test_http_llm_retries_invalid_then_valid() -> None:
    payloads = [
        {"choices": [{"message": {"content": json.dumps({"summary": "Nope"})}}]},
        {"choices": [{"message": {"content": json.dumps({"summary": VALID})}}]},
    ]

    class FakeClient:
        def post(self, url, json, headers):
            assert "chat/completions" in url
            assert "Authorization" in headers
            return httpx.Response(200, json=payloads.pop(0))

    curator = HttpLlmCurator(
        Settings(
            cf_account_id="acct",
            cf_ai_gateway_id="gw",
            llm_provider_api_key="token",
        ),
        http_client=FakeClient(),
    )
    assert curator.summarise(TRADE, ["trading", "finance", "daily"]).startswith("A daily export")


def test_http_llm_uses_workers_ai_binding_when_present() -> None:
    class FakeAI:
        def run(self, model, payload):
            assert model == "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
            assert payload["messages"][0]["role"] == "system"
            return {"response": json.dumps({"summary": VALID})}

    curator = HttpLlmCurator(Settings(llm_provider_api_key="token"), ai_binding=FakeAI())
    assert curator.summarise(TRADE, ["trading"]) == SummaryResult(summary=VALID).summary


def test_message_text_reads_openai_and_workers_shapes() -> None:
    assert _message_text({"response": VALID}) == VALID
    assert _message_text({"choices": [{"message": {"content": VALID}}]}) == VALID


def test_worker_curator_keeps_hybrid_and_partial_union() -> None:
    curator = get_worker_curator(Settings(cf_account_id="acct", llm_provider_api_key="token"))
    assert isinstance(curator, HybridCurator)

    class BoomClassifier:
        def classify(self, payload, dataset_id=""):
            raise RuntimeError("jev down")

    class OkSummary:
        def summarise(self, payload, tags, dataset_id=""):
            return VALID

    result = HybridCurator(BoomClassifier(), OkSummary()).curate(TRADE)
    assert result.status == "partial"
    assert result.tags == []
    assert result.summary.startswith("A daily export")

    class OkTags:
        def classify(self, payload, dataset_id=""):
            return ["trading"]

    class BoomSummary:
        def summarise(self, payload, tags, dataset_id=""):
            raise RuntimeError("llama down")

    failed_summary = HybridCurator(OkTags(), BoomSummary()).curate(TRADE)
    assert failed_summary.status == "partial"
    assert failed_summary.tags == ["trading"]
    assert failed_summary.summary == PLACEHOLDER_SUMMARY


def test_settings_from_env_reads_binding_names_only() -> None:
    settings = settings_from_env(
        SimpleNamespace(
            CF_ACCOUNT_ID="acct",
            CF_AI_GATEWAY_ID="gw",
            LLM_PROVIDER_API_KEY="token",
            LLM_MODEL="",
            CLASSIFIER_MODEL="",
        )
    )
    assert settings.llm_ready is True
    assert settings.workers_ai_model() == "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
