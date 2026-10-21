import pytest
from fastapi.testclient import TestClient

from app.curation.keyword import KeywordCurator
from app.main import create_app
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.services.datasets import DatasetService


@pytest.fixture
def client() -> TestClient:
    service = DatasetService(InMemoryDatasetStore(SEED_DATASETS), KeywordCurator())
    return TestClient(create_app(service))
