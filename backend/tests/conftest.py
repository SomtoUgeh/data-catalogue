import pytest
from fastapi.testclient import TestClient

from app.curation.base import Curator
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import CurationResult, DatasetCreate


class StubCurator(Curator):
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        return CurationResult(
            tags=["trading", "finance", "settlements", "daily"],
            summary="A daily export of confirmed trades covering counterparties and settlements.",
        )


@pytest.fixture
def repository() -> DatasetRepository:
    return DatasetRepository()


@pytest.fixture
def client(repository: DatasetRepository) -> TestClient:
    app = create_app(repository=repository, curator=StubCurator())
    return TestClient(app)
