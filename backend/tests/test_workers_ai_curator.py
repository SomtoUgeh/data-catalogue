import asyncio
import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.curation.workers_ai import WorkersAiCurator, scores_from_answers, tags_from_scores
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.services.datasets import DatasetService
from tests.payloads import TRADE_CONFIRMATIONS

CLEF_ANSWERS = {
    "trading": {"noul": 0.97},
    "daily": {"noul": 0.95},
    "finance": {"noul": 0.87},
    "settlements": {"noul": 0.69},
    "inventory": {"noul": 0.01},
    "PII": {"noul": 0.07},
}
CLEF_TAGS = ["trading", "daily", "finance", "settlements"]
SUMMARY = "A daily export of confirmed trade records covering instruments, counterparties, and settlement dates."
GOOD_REPLIES = {"clef": {"answers": CLEF_ANSWERS}, "llama": {"response": {"summary": SUMMARY}}}


class FakeAi:
    """Stands in for the Workers AI binding: one canned reply per model, and a log of the calls.

    `failures` lists errors to raise for a model, one per call, before its reply is returned.
    """

    def __init__(self, replies: dict[str, Any], failures: Mapping[str, Sequence[Exception]] | None = None) -> None:
        self.replies = replies
        self.failures = {model: list(errors) for model, errors in (failures or {}).items()}
        self.calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    async def run(self, model: str, request: dict[str, Any], options: dict[str, Any]) -> Any:
        self.calls.append((model, request, options))
        if self.failures.get(model):
            raise self.failures[model].pop(0)
        return self.replies[model]


class SlowAi(FakeAi):
    async def run(self, model: str, request: dict[str, Any], options: dict[str, Any]) -> Any:
        await asyncio.sleep(1)
        return await super().run(model, request, options)


def client_with(ai: FakeAi, timeout_seconds: float = 5, gateway_id: str | None = None) -> TestClient:
    curator = WorkersAiCurator(
        ai, classifier_model="clef", summary_model="llama", gateway_id=gateway_id, timeout_seconds=timeout_seconds
    )
    return TestClient(create_app(DatasetService(InMemoryDatasetStore(SEED_DATASETS), curator)))


def curation_events(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    events = [json.loads(record.getMessage()) for record in caplog.records if record.name.startswith("app.")]
    return [event for event in events if event["event"] == "curation"]


def test_clef_picks_the_tags_and_the_chat_model_writes_the_summary() -> None:
    ai = FakeAi(GOOD_REPLIES)

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == CLEF_TAGS
    assert created["summary"] == SUMMARY
    assert created["curation_status"] == "ok"
    (clef_model, clef_request, _), (llama_model, llama_request, _) = ai.calls
    assert clef_model == "clef"
    assert set(clef_request["questions"]) >= {"trading", "PII", "daily"}
    assert llama_model == "llama"
    assert "Tags: trading, daily, finance, settlements" in llama_request["messages"][-1]["content"]


def test_tags_are_ordered_by_probability_and_capped() -> None:
    ranked = ["HR", "finance", "daily", "PII", "trading", "products"]
    answers = {tag: {"noul": 1 - i / 100} for i, tag in enumerate(ranked)}

    assert tags_from_scores(scores_from_answers(answers)) == ["HR", "finance", "daily", "PII", "trading"]


LONG_SUMMARY = " ".join(["word"] * 26)


@pytest.mark.parametrize(
    "llama_reply",
    [{"response": {"text": "not a summary"}}, {"response": {"summary": LONG_SUMMARY}}],
    ids=["wrong shape", "too long"],
)
def test_invalid_summary_keeps_the_tags_and_saves_as_failed(llama_reply: dict[str, Any]) -> None:
    client = client_with(FakeAi({**GOOD_REPLIES, "llama": llama_reply}))

    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    created = response.json()
    assert created["tags"] == CLEF_TAGS
    assert created["summary"] == ""
    assert created["curation_status"] == "failed"
    assert created in client.get("/datasets").json()


def test_classifier_failure_saves_without_tags() -> None:
    ai = FakeAi(GOOD_REPLIES, failures={"clef": [RuntimeError("AiError: 5007: No such model")]})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == []
    assert created["curation_status"] == "failed"
    assert len(ai.calls) == 1  # a permanent error is not retried, and the summary is not attempted


def test_transient_error_is_retried_once() -> None:
    ai = FakeAi(GOOD_REPLIES, failures={"llama": [RuntimeError("AiError: 3040: Out of capacity")]})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["curation_status"] == "ok"
    assert [model for model, _, _ in ai.calls] == ["clef", "llama", "llama"]


def test_slow_model_times_out_and_saves_as_failed() -> None:
    response = client_with(SlowAi(GOOD_REPLIES), timeout_seconds=0.05).post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    assert response.json()["curation_status"] == "failed"


def test_no_matching_tags_still_keeps_the_summary() -> None:
    unsure = {tag: {"noul": 0.2} for tag in CLEF_ANSWERS}
    ai = FakeAi({**GOOD_REPLIES, "clef": {"answers": unsure}})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == []
    assert created["summary"] == SUMMARY
    assert created["curation_status"] == "ok"


def test_calls_go_through_ai_gateway_tagged_with_the_logged_curation_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    ai = FakeAi(GOOD_REPLIES)

    client_with(ai, gateway_id="catalogue").post("/datasets", json=TRADE_CONFIRMATIONS)

    (event,) = curation_events(caplog)
    assert [options for _, _, options in ai.calls] == [
        {"gateway": {"id": "catalogue", "metadata": {"curation_id": event["curation_id"], "step": "classify"}}},
        {"gateway": {"id": "catalogue", "metadata": {"curation_id": event["curation_id"], "step": "summary"}}},
    ]


def test_each_curation_logs_one_event_with_scores_timings_and_outcome(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    failures = {"llama": [RuntimeError("AiError: 3040: Out of capacity"), RuntimeError("AiError: 3040: again")]}

    client_with(FakeAi(GOOD_REPLIES, failures), gateway_id="catalogue").post("/datasets", json=TRADE_CONFIRMATIONS)

    (event,) = curation_events(caplog)
    assert event["outcome"] == "incomplete"
    assert event["error"] == "RuntimeError: AiError: 3040: again"
    assert event["summary_retried_after"] == "RuntimeError: AiError: 3040: Out of capacity"
    assert event["tags"] == CLEF_TAGS
    assert event["scores"]["inventory"] == 0.01
    assert {"curation_id", "classify_ms", "summary_ms"} <= event.keys()
