from abc import ABC, abstractmethod
from typing import Protocol

from app.curation.outcome import CurationOutcome
from app.schemas import DatasetCreate


class CurationError(Exception):
    """The curator could not produce a valid tags/summary result."""


class Curator(ABC):
    @abstractmethod
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationOutcome:
        """Return a typed curation outcome. Raise only for unexpected errors."""


class Summarizer(Protocol):
    def summarise(self, payload: DatasetCreate, tags: list[str], dataset_id: str = "") -> str: ...
