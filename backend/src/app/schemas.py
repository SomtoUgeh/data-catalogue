from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalText = Annotated[str, StringConstraints(strip_whitespace=True)]

CurationStatus = Literal["ok", "failed"]


class DatasetCreate(BaseModel):
    """Request body for POST /datasets."""

    name: RequiredText
    owner: OptionalText = ""
    description: RequiredText


class DatasetFields(BaseModel):
    """A curated dataset before the store has assigned it an id."""

    name: str
    owner: str
    description: str
    tags: list[str]
    summary: str
    curation_status: CurationStatus


class Dataset(DatasetFields):
    """A stored dataset, as returned by every endpoint."""

    id: str
