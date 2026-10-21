import pytest
from fastapi.testclient import TestClient

from app.curation.keyword import KeywordCurator
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.schemas import Dataset
from app.services.datasets import DatasetService
from tests.payloads import TRADE_CONFIRMATIONS


def test_get_returns_the_three_seeded_datasets(client: TestClient) -> None:
    response = client.get("/datasets")

    assert response.status_code == 200
    assert [dataset["name"] for dataset in response.json()] == [
        "Customer Transactions",
        "Product Inventory",
        "Employee Directory",
    ]


def test_post_saves_the_dataset_with_curated_tags_and_summary(client: TestClient) -> None:
    response = client.post("/datasets", json=TRADE_CONFIRMATIONS)

    assert response.status_code == 201
    created = response.json()
    assert created == {
        "id": "4",
        **TRADE_CONFIRMATIONS,
        "tags": ["trading", "finance", "settlements", "daily"],
        "summary": (
            "A daily trading dataset covering instrument type, counterparty, notional value, and settlement date."
        ),
        "curation_status": "ok",
    }
    assert created in client.get("/datasets").json()


def test_delete_removes_the_dataset(client: TestClient) -> None:
    response = client.delete("/datasets/1")

    assert response.status_code == 200
    assert response.json()["id"] == "1"
    assert "1" not in [dataset["id"] for dataset in client.get("/datasets").json()]


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    response = client.delete("/datasets/999")

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset '999' not found"}


@pytest.mark.parametrize(
    ("payload", "invalid_fields"),
    [
        ({"owner": "Middle Office", "description": "Daily trades."}, ["name"]),
        ({"name": "Trades", "owner": "Middle Office"}, ["description"]),
        ({"name": "   ", "description": "Daily trades."}, ["name"]),
        ({"name": "", "description": ""}, ["name", "description"]),
    ],
)
def test_post_with_missing_or_blank_fields_returns_400(
    client: TestClient, payload: dict[str, str], invalid_fields: list[str]
) -> None:
    response = client.post("/datasets", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "error": "Validation failed",
        "fields": [{"field": field, "message": f"{field} is required"} for field in invalid_fields],
    }
    assert len(client.get("/datasets").json()) == 3


class BrokenStore(InMemoryDatasetStore):
    async def list(self) -> list[Dataset]:
        raise RuntimeError("database is unavailable")


def test_unexpected_errors_return_500_with_the_standard_error_shape() -> None:
    app = create_app(DatasetService(BrokenStore(SEED_DATASETS), KeywordCurator()))
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/datasets")

    assert response.status_code == 500
    assert response.json() == {"error": "Internal server error"}
