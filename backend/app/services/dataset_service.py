from app.curation.base import CurationError, Curator
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import Dataset, DatasetCreate

PLACEHOLDER_TAGS = ["uncurated"]
PLACEHOLDER_SUMMARY = (
    "Curation unavailable. Tags and summary will appear once tagging succeeds."
)


class DatasetNotFoundError(Exception):
    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Dataset with id '{dataset_id}' was not found.")


class DatasetService:
    def __init__(self, repository: DatasetRepository, curator: Curator) -> None:
        self.repository = repository
        self.curator = curator

    def list_datasets(self) -> list[Dataset]:
        return self.repository.list_all()

    def create_dataset(self, payload: DatasetCreate) -> Dataset:
        dataset_id = self.repository.next_id()
        try:
            curated = self.curator.curate(payload, dataset_id=dataset_id)
            tags, summary, status = curated.tags, curated.summary, "ok"
        except Exception:
            tags, summary, status = PLACEHOLDER_TAGS, PLACEHOLDER_SUMMARY, "failed"

        dataset = Dataset(
            id=dataset_id,
            name=payload.name,
            owner=payload.owner,
            description=payload.description,
            tags=tags,
            summary=summary,
            curation_status=status,
        )
        return self.repository.add(dataset)

    def delete_dataset(self, dataset_id: str) -> Dataset:
        deleted = self.repository.delete(dataset_id)
        if deleted is None:
            raise DatasetNotFoundError(dataset_id)
        return deleted
