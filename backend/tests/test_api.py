from app.curation.base import CurationError, Curator
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import CurationResult, DatasetCreate
from app.services.dataset_service import PLACEHOLDER_SUMMARY, PLACEHOLDER_TAGS
from fastapi.testclient import TestClient

TRADE_CONFIRMATIONS = {
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": (
        "Daily export of confirmed trades including instrument type, "
        "counterparty, notional value, and settlement date."
    ),
}

SEEDED_IDS = {"1", "2", "3"}
SEEDED_NAMES = {
    "Customer Transactions",
    "Product Inventory",
    "Employee Directory",
}


class FailingCurator(Curator):
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        raise CurationError("forced failure")


def test_get_datasets_returns_seeded_entries(client: TestClient) -> None:
    response = client.get("/datasets")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert {item["id"] for item in body} == SEEDED_IDS
    assert {item["name"] for item in body} == SEEDED_NAMES
    customer = next(item for item in body if item["id"] == "1")
    assert customer["tags"] == ["finance", "transactions", "PII", "daily"]
    assert customer["owner"] == "Finance Team"


def test_post_trade_confirmations_returns_201_with_curation(client: TestClient) -> None:
    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == TRADE_CONFIRMATIONS["name"]
    assert body["owner"] == TRADE_CONFIRMATIONS["owner"]
    assert body["description"] == TRADE_CONFIRMATIONS["description"]
    assert body["curation_status"] == "ok"
    assert set(body["tags"]) >= {"trading", "finance", "settlements", "daily"}
    assert body["summary"]
    assert "trade" in body["summary"].lower() or "Trade" in body["summary"]


def test_delete_dataset_returns_200_and_removes_entry(client: TestClient) -> None:
    response = client.delete("/datasets/1")
    assert response.status_code == 200
    assert response.json()["id"] == "1"

    remaining = client.get("/datasets")
    assert remaining.status_code == 200
    assert all(item["id"] != "1" for item in remaining.json())
    assert len(remaining.json()) == 2


def test_post_missing_name_returns_400(client: TestClient) -> None:
    response = client.post(
        "/datasets",
        json={"owner": "Middle Office", "description": "Daily export of trades."},
    )
    assert response.status_code == 400
    assert "name" in response.json()["error"]


def test_post_missing_description_returns_400(client: TestClient) -> None:
    response = client.post(
        "/datasets",
        json={"name": "Trade Confirmations", "owner": "Middle Office"},
    )
    assert response.status_code == 400
    assert "description" in response.json()["error"]


def test_post_blank_name_returns_400(client: TestClient) -> None:
    response = client.post(
        "/datasets",
        json={"name": "   ", "owner": "Middle Office", "description": "Daily export of trades."},
    )
    assert response.status_code == 400
    assert "name" in response.json()["error"]


def test_post_blank_description_returns_400(client: TestClient) -> None:
    response = client.post(
        "/datasets",
        json={"name": "Trade Confirmations", "owner": "Middle Office", "description": ""},
    )
    assert response.status_code == 400
    assert "description" in response.json()["error"]


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    response = client.delete("/datasets/missing")
    assert response.status_code == 404
    assert "missing" in response.json()["error"]


def test_create_still_saves_when_curation_fails() -> None:
    app = create_app(repository=DatasetRepository(), curator=FailingCurator())
    client = TestClient(app)

    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == TRADE_CONFIRMATIONS["name"]
    assert body["tags"] == PLACEHOLDER_TAGS
    assert body["summary"] == PLACEHOLDER_SUMMARY
    assert body["curation_status"] == "failed"

    listed = client.get("/datasets").json()
    assert any(item["id"] == body["id"] and item["curation_status"] == "failed" for item in listed)
