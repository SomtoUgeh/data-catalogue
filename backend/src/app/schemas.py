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


class ErrorResponse(BaseModel):
    """Body of every error response, for example a 404."""

    error: str


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    """Body of a 400. `fields` names each invalid request field so the UI can show errors inline."""

    fields: list[FieldError]
