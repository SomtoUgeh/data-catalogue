import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.curation.workers_ai import WorkersAiCurator, tags_from_answers
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
SUMMARY = "A daily export of confirmed trade records covering instruments, counterparties, and settlement dates."


class FakeAi:
    """Stands in for the Workers AI binding: one canned reply per model, and a log of the requests."""

    def __init__(self, replies: dict[str, Any]) -> None:
        self.replies = replies
        self.requests: list[tuple[str, dict[str, Any]]] = []

    async def run(self, model: str, request: dict[str, Any]) -> Any:
        self.requests.append((model, request))
        return self.replies[model]


class SlowAi(FakeAi):
    async def run(self, model: str, request: dict[str, Any]) -> Any:
        await asyncio.sleep(1)
        return await super().run(model, request)


def client_with(ai: FakeAi, timeout_seconds: float = 5) -> TestClient:
    curator = WorkersAiCurator(ai, classifier_model="clef", summary_model="llama", timeout_seconds=timeout_seconds)
    return TestClient(create_app(DatasetService(InMemoryDatasetStore(SEED_DATASETS), curator)))


def test_clef_picks_the_tags_and_the_chat_model_writes_the_summary() -> None:
    ai = FakeAi({"clef": {"answers": CLEF_ANSWERS}, "llama": {"response": {"summary": SUMMARY}}})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == ["trading", "daily", "finance", "settlements"]
    assert created["summary"] == SUMMARY
    assert created["curation_status"] == "ok"
    (clef_model, clef_request), (llama_model, llama_request) = ai.requests
    assert clef_model == "clef"
    assert set(clef_request["questions"]) >= {"trading", "PII", "daily"}
    assert llama_model == "llama"
    assert "Tags: trading, daily, finance, settlements" in llama_request["messages"][-1]["content"]


def test_tags_are_ordered_by_probability_and_capped() -> None:
    ranked = ["HR", "finance", "daily", "PII", "trading", "products"]
    answers = {tag: {"noul": 1 - i / 100} for i, tag in enumerate(ranked)}

    assert tags_from_answers(answers) == ["HR", "finance", "daily", "PII", "trading"]


LONG_SUMMARY = " ".join(["word"] * 26)


@pytest.mark.parametrize(
    "llama_reply",
    [{"response": {"text": "not a summary"}}, {"response": {"summary": LONG_SUMMARY}}],
    ids=["wrong shape", "too long"],
)
def test_invalid_summary_still_saves_the_dataset_as_failed(llama_reply: dict[str, Any]) -> None:
    ai = FakeAi({"clef": {"answers": CLEF_ANSWERS}, "llama": llama_reply})
    client = client_with(ai)

    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    created = response.json()
    assert created["tags"] == []
    assert created["summary"] == ""
    assert created["curation_status"] == "failed"
    assert created in client.get("/datasets").json()


def test_slow_model_times_out_and_saves_the_dataset_as_failed() -> None:
    ai = SlowAi({"clef": {"answers": CLEF_ANSWERS}, "llama": {"response": {"summary": SUMMARY}}})

    response = client_with(ai, timeout_seconds=0.05).post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    assert response.json()["curation_status"] == "failed"


def test_no_matching_tags_still_keeps_the_summary() -> None:
    unsure = {tag: {"noul": 0.2} for tag in CLEF_ANSWERS}
    ai = FakeAi({"clef": {"answers": unsure}, "llama": {"response": {"summary": SUMMARY}}})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == []
    assert created["summary"] == SUMMARY
    assert created["curation_status"] == "ok"
