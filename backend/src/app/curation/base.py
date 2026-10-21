from typing import Annotated, Protocol

from pydantic import BaseModel, Field, StringConstraints

from app.schemas import DatasetCreate

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


class CurationResult(BaseModel):
    tags: list[Tag] = Field(min_length=1, max_length=6)
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class Curator(Protocol):
    async def curate(self, dataset: DatasetCreate) -> CurationResult: ...
