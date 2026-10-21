import logging

from app.curation.base import CurationResult, Curator
from app.repositories.base import DatasetStore
from app.schemas import Dataset, DatasetCreate, DatasetFields

logger = logging.getLogger(__name__)


class DatasetNotFoundError(Exception):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset '{dataset_id}' not found")
        self.dataset_id = dataset_id


class DatasetService:
    def __init__(self, store: DatasetStore, curator: Curator) -> None:
        self._store = store
        self._curator = curator

    async def list_datasets(self) -> list[Dataset]:
        return await self._store.list_all()

    async def create_dataset(self, data: DatasetCreate) -> Dataset:
        curation = await self._curate(data)
        return await self._store.add(
            DatasetFields(
                name=data.name,
                owner=data.owner,
                description=data.description,
                tags=curation.tags if curation else [],
                summary=curation.summary if curation else "",
                curation_status="ok" if curation else "failed",
            )
        )

    async def delete_dataset(self, dataset_id: str) -> Dataset:
        dataset = await self._store.delete(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    async def _curate(self, data: DatasetCreate) -> CurationResult | None:
        # Curation is best effort: any failure (network, timeout, invalid model output)
        # must not stop the dataset from being saved.
        try:
            return await self._curator.curate(data)
        except Exception:
            logger.exception("Curation failed for dataset %r", data.name)
            return None
