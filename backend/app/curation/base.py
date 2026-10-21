from abc import ABC, abstractmethod

from app.schemas import CurationResult, DatasetCreate


class CurationError(Exception):
    """The curator could not produce a valid tags/summary result."""


class MalformedCurationError(CurationError):
    """The model responded, but the body was not valid curated JSON."""


class Curator(ABC):
    @abstractmethod
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        """Return structured curation, or raise CurationError."""
