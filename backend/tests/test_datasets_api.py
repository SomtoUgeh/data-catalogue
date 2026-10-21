import pytest
from fastapi.testclient import TestClient

from app.curation.keyword import KeywordCurator
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.schemas import Dataset
from app.services.datasets import DatasetService
from tests.payloads import TRADE_CONFIRMATIONS


def test_get_returns_the_three_seeded_datasets_newest_first(client: TestClient) -> None:
    response = client.get("/datasets")

    assert response.status_code == 200
    assert [dataset["name"] for dataset in response.json()] == [
        "Employee Directory",
        "Product Inventory",
        "Customer Transactions",
    ]


def test_get_pages_with_limit_and_before(client: TestClient) -> None:
    first = client.get("/datasets", params={"limit": 2}).json()
    rest = client.get("/datasets", params={"limit": 2, "before": first[-1]["id"]}).json()

    assert [dataset["id"] for dataset in first] == ["3", "2"]
    assert [dataset["id"] for dataset in rest] == ["1"]


@pytest.mark.parametrize(
    ("params", "field_error"),
    [
        ({"limit": 0}, {"field": "limit", "message": "Limit: Input should be greater than or equal to 1"}),
        ({"limit": 101}, {"field": "limit", "message": "Limit: Input should be less than or equal to 100"}),
        ({"before": "abc"}, {"field": "before", "message": "Before must be a dataset id"}),
    ],
)
def test_get_with_invalid_paging_returns_400(
    client: TestClient, params: dict[str, str | int], field_error: dict[str, str]
) -> None:
    response = client.get("/datasets", params=params)

    assert response.status_code == 400
    assert response.json() == {"error": "Validation failed", "fields": [field_error]}


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
        "fields": [{"field": field, "message": f"{field.capitalize()} is required"} for field in invalid_fields],
    }
    assert len(client.get("/datasets").json()) == 3


def test_post_with_a_too_long_field_returns_400_with_the_limit(client: TestClient) -> None:
    response = client.post("/datasets", json={**TRADE_CONFIRMATIONS, "name": "x" * 201})

    assert response.status_code == 400
    assert response.json()["fields"] == [{"field": "name", "message": "Name must be at most 200 characters"}]


@pytest.mark.parametrize(
    "request_options",
    [
        {"content": "{", "headers": {"Content-Type": "application/json"}},
        {"json": ["not", "an", "object"]},
        {},
    ],
    ids=["malformed JSON", "array", "no body"],
)
def test_post_without_a_json_object_returns_400_on_the_body(
    client: TestClient, request_options: dict[str, object]
) -> None:
    response = client.post("/datasets", **request_options)  # pyright: ignore[reportArgumentType]

    assert response.status_code == 400
    assert response.json()["fields"] == [{"field": "body", "message": "Request body must be a JSON object"}]


def test_post_with_a_wrong_type_names_the_field(client: TestClient) -> None:
    response = client.post("/datasets", json={"name": 5, "description": "Daily trades."})

    assert response.json()["fields"] == [{"field": "name", "message": "Name: Input should be a valid string"}]


def test_unknown_routes_and_methods_use_the_standard_error_shape(client: TestClient) -> None:
    assert client.get("/nope").json() == {"error": "Not Found"}
    wrong_method = client.put("/datasets")
    assert wrong_method.status_code == 405
    assert wrong_method.json() == {"error": "Method Not Allowed"}


def test_openapi_documents_400_instead_of_422(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    responses = [op["responses"] for path in schema["paths"].values() for op in path.values()]
    assert all("422" not in codes for codes in responses)
    assert "400" in schema["paths"]["/datasets"]["post"]["responses"]
    assert "429" in schema["paths"]["/datasets"]["post"]["responses"]


class BrokenStore(InMemoryDatasetStore):
    async def list_page(self, limit: int, before: int | None) -> list[Dataset]:
        raise RuntimeError("database is unavailable")


def test_unexpected_errors_return_500_with_the_standard_error_shape() -> None:
    app = create_app(DatasetService(BrokenStore(SEED_DATASETS), KeywordCurator()))
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/datasets")

    assert response.status_code == 500
    assert response.json() == {"error": "Internal server error"}
