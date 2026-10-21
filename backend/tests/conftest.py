import pytest
from app.curation.base import Curator
from app.curation.outcome import CurationOk, CurationOutcome
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import DatasetCreate
from fastapi.testclient import TestClient


class StubCurator(Curator):
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationOutcome:
        return CurationOk(
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
