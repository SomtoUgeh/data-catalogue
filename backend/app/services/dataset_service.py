import logging
import re
import time

from app.curation.base import Curator
from app.curation.outcome import CurationFailed, PLACEHOLDER_SUMMARY
from app.repositories.dataset_repository import DatasetRepository
from app.schemas import Dataset, DatasetCreate

logger = logging.getLogger("uvicorn.error")

PLACEHOLDER_TAGS: list[str] = []

_BEARER_RE = re.compile(r"(?i)\bbearer\s+\S+")
_KEY_RE = re.compile(r"(?i)\b(?:authorization|api[_-]?key)\s*[=:]\s*\S+")


def _safe_error(exc: Exception) -> str:
    """Log class, HTTP status, and a short body — never tokens or keys."""
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    body = ""
    if response is not None:
        try:
            body = (getattr(response, "text", None) or "")[:400]
        except Exception:
            body = ""
    raw = f"{type(exc).__name__} status={status} {body or str(exc)[:400]}"
    return _KEY_RE.sub("[redacted]", _BEARER_RE.sub("[redacted]", raw))


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
        curator_name = type(self.curator).__name__
        logger.info("curating dataset_id=%s curator=%s name=%s", dataset_id, curator_name, payload.name)
        started = time.perf_counter()
        try:
            outcome = self.curator.curate(payload, dataset_id=dataset_id)
        except Exception as exc:
            outcome = CurationFailed()
            logger.warning(
                "curation_status=failed dataset_id=%s curator=%s latency_ms=%d error=%s",
                dataset_id,
                curator_name,
                int((time.perf_counter() - started) * 1000),
                _safe_error(exc),
            )
        else:
            logger.info(
                "curation_status=%s dataset_id=%s curator=%s tags=%s latency_ms=%d",
                outcome.status,
                dataset_id,
                curator_name,
                outcome.tags,
                int((time.perf_counter() - started) * 1000),
            )

        dataset = Dataset(
            id=dataset_id,
            name=payload.name,
            owner=payload.owner,
            description=payload.description,
            tags=outcome.tags,
            summary=outcome.summary,
            curation_status=outcome.status,
        )
        return self.repository.add(dataset)

    def delete_dataset(self, dataset_id: str) -> Dataset:
        deleted = self.repository.delete(dataset_id)
        if deleted is None:
            raise DatasetNotFoundError(dataset_id)
        return deleted
