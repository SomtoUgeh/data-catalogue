import pytest
from fastapi.testclient import TestClient

from app.curation.keyword import KeywordCurator
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository


@pytest.fixture
def repository() -> DatasetRepository:
    return DatasetRepository()


@pytest.fixture
def client(repository: DatasetRepository) -> TestClient:
    app = create_app(repository=repository, curator=KeywordCurator())
    return TestClient(app)
