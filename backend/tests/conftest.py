import pytest
from fastapi.testclient import TestClient

from app.curation.keyword import KeywordCurator
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.services.dataset_service import DatasetService

TRADE_CONFIRMATIONS = {
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": (
        "Daily export of confirmed trades including instrument type, counterparty, notional value, and settlement date."
    ),
}


@pytest.fixture
def client() -> TestClient:
    service = DatasetService(InMemoryDatasetStore(SEED_DATASETS), KeywordCurator())
    return TestClient(create_app(service))
