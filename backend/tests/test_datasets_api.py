import pytest
from fastapi.testclient import TestClient

from tests.conftest import TRADE_CONFIRMATIONS


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
    assert response.json() == {"detail": "Dataset '999' not found"}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"owner": "Middle Office", "description": "Daily trades."}, "name is required"),
        ({"name": "Trades", "owner": "Middle Office"}, "description is required"),
        ({"name": "   ", "description": "Daily trades."}, "name is required"),
        ({"name": "", "description": ""}, "name is required; description is required"),
    ],
)
def test_post_with_missing_or_blank_fields_returns_400(
    client: TestClient, payload: dict[str, str], message: str
) -> None:
    response = client.post("/datasets", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": message}
    assert len(client.get("/datasets").json()) == 3
