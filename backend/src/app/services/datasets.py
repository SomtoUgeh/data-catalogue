import logging

from app.curation.base import Curator, IncompleteCurationError
from app.logs import current_traceback, log_event
from app.repositories.base import DatasetStore
from app.schemas import CurationStatus, Dataset, DatasetCreate, DatasetFields

logger = logging.getLogger(__name__)


class DatasetNotFoundError(Exception):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset '{dataset_id}' not found")
        self.dataset_id = dataset_id


class DatasetService:
    def __init__(self, store: DatasetStore, curator: Curator) -> None:
        self._store = store
        self._curator = curator

    async def list_datasets(self, limit: int, before: int | None = None) -> list[Dataset]:
        return await self._store.list_page(limit, before)

    async def create_dataset(self, data: DatasetCreate) -> Dataset:
        tags, summary, status = await self._curate(data)
        return await self._store.add(
            DatasetFields(
                name=data.name,
                owner=data.owner,
                description=data.description,
                tags=tags,
                summary=summary,
                curation_status=status,
            )
        )

    async def delete_dataset(self, dataset_id: str) -> Dataset:
        dataset = await self._store.delete(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    async def _curate(self, data: DatasetCreate) -> tuple[list[str], str, CurationStatus]:
        # Curation is best effort: any failure (network, timeout, invalid model output) must not stop the
        # dataset from being saved. Tags chosen before a failure are kept; the summary is left empty.
        try:
            result = await self._curator.curate(data)
            return result.tags, result.summary, "ok"
        except IncompleteCurationError as exc:
            log_event(
                logger,
                logging.WARNING,
                "curation_incomplete",
                dataset=data.name,
                tags=exc.tags,
                traceback=current_traceback(),
            )
            return exc.tags, "", "failed"
        except Exception:
            log_event(logger, logging.ERROR, "curation_failed", dataset=data.name, traceback=current_traceback())
            return [], "", "failed"
