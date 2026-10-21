import json
from typing import Any

from fastapi.testclient import TestClient

from app.curation.workers_ai import WorkersAiCurator
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.services.dataset_service import DatasetService
from tests.conftest import TRADE_CONFIRMATIONS

CURATED = {
    "tags": ["trading", "finance", "settlements", "daily"],
    "summary": "A daily export of confirmed trade records covering instruments, counterparties, and settlement dates.",
}


class FakeAi:
    """Stands in for the Workers AI binding. Records the request and returns a fixed reply."""

    def __init__(self, reply: Any) -> None:
        self.reply = reply
        self.requests: list[tuple[str, dict[str, Any]]] = []

    async def run(self, model: str, request: dict[str, Any]) -> Any:
        self.requests.append((model, request))
        return self.reply


def client_with(ai: FakeAi) -> TestClient:
    service = DatasetService(InMemoryDatasetStore(SEED_DATASETS), WorkersAiCurator(ai, "test-model"))
    return TestClient(create_app(service))


def test_asks_the_model_for_json_and_stores_its_reply() -> None:
    ai = FakeAi({"response": CURATED})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == CURATED["tags"]
    assert created["summary"] == CURATED["summary"]
    assert created["curation_status"] == "ok"
    model, request = ai.requests[0]
    assert model == "test-model"
    assert request["response_format"]["type"] == "json_schema"
    assert "Trade Confirmations" in request["messages"][-1]["content"]


def test_accepts_the_json_object_as_a_string() -> None:
    ai = FakeAi({"response": json.dumps(CURATED)})

    created = client_with(ai).post("/datasets", json=TRADE_CONFIRMATIONS).json()

    assert created["tags"] == CURATED["tags"]


def test_malformed_reply_still_saves_the_dataset_as_failed() -> None:
    ai = FakeAi({"response": {"labels": "not a list"}})
    client = client_with(ai)

    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    created = response.json()
    assert created["tags"] == []
    assert created["summary"] == ""
    assert created["curation_status"] == "failed"
    assert created in client.get("/datasets").json()
