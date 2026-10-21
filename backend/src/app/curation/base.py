"""The curation interface DatasetService depends on.

keyword.py implements it without AI (local runs and tests); workers_ai.py implements it with Clef and
Llama on Cloudflare. Both read the tag vocabulary from tags.py.
"""

from typing import Annotated, Protocol

from pydantic import BaseModel, Field, StringConstraints

from app.schemas import DatasetCreate

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


class CurationResult(BaseModel):
    """Tags may be empty when nothing in the vocabulary fits; the summary is always required."""

    tags: list[Tag] = Field(max_length=6)
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class IncompleteCurationError(Exception):
    """Raised when a curator chose tags but could not write the summary. The tags are still worth saving."""

    def __init__(self, tags: list[str]) -> None:
        super().__init__(f"Curation stopped after choosing tags {tags}")
        self.tags = tags


class Curator(Protocol):
    async def curate(self, dataset: DatasetCreate) -> CurationResult: ...
