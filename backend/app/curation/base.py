from abc import ABC, abstractmethod

from app.curation.outcome import CurationOutcome
from app.schemas import DatasetCreate


class CurationError(Exception):
    """The curator could not produce a valid tags/summary result."""


class MalformedCurationError(CurationError):
    """The model responded, but the body was not valid curated JSON."""


class Curator(ABC):
    @abstractmethod
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationOutcome:
        """Return a typed curation outcome. Raise only for unexpected errors."""
