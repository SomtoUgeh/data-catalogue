from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.curation.tags import MAX_TAGS

TRADE_CONFIRMATIONS_CREATE: dict[str, Any] = {
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": (
        "Daily export of confirmed trades including instrument type, "
        "counterparty, notional value, and settlement date."
    ),
}

TRADE_CONFIRMATIONS_DATASET: dict[str, Any] = {
    "id": "4",
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": TRADE_CONFIRMATIONS_CREATE["description"],
    "tags": ["trading", "finance", "settlements", "daily"],
    "summary": "A daily export of confirmed trades covering counterparties and settlements.",
    "curation_status": "ok",
}

VALIDATION_ERROR_EXAMPLE: dict[str, Any] = {
    "error": "Validation failed",
    "fields": [{"field": "name", "message": "name is required"}],
}
NOT_FOUND_ERROR_EXAMPLE: dict[str, Any] = {"error": "Dataset with id 'missing' was not found."}


class DatasetCreate(BaseModel):
    """Body for registering a dataset. Name, owner, and description are required."""

    model_config = ConfigDict(
        title="DatasetCreate",
        str_strip_whitespace=True,
        json_schema_extra={"examples": [TRADE_CONFIRMATIONS_CREATE]},
    )

    name: str = Field(min_length=1, examples=["Trade Confirmations"])
    owner: str = Field(min_length=1, examples=["Middle Office"])
    description: str = Field(
        min_length=1,
        examples=[TRADE_CONFIRMATIONS_CREATE["description"]],
    )


class SummaryResult(BaseModel):
    """Llama output after Jev has already chosen tags."""

    model_config = ConfigDict(title="SummaryResult")

    summary: str

    @field_validator("summary")
    @classmethod
    def clean_summary(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text.startswith("A "):
            raise ValueError("summary must be one sentence starting with 'A '")
        if text.count(".") > 1:
            raise ValueError("summary must be a single sentence")
        words = text.rstrip(".").split()
        if not (3 <= len(words) <= 25):
            raise ValueError("summary must be one sentence under 25 words")
        return text if text.endswith(".") else f"{text}."


class Dataset(BaseModel):
    """A registered catalogue entry, including curator tags and summary."""

    model_config = ConfigDict(
        title="Dataset",
        json_schema_extra={"examples": [TRADE_CONFIRMATIONS_DATASET]},
    )

    id: str = Field(examples=["4"])
    name: str = Field(examples=["Trade Confirmations"])
    owner: str = Field(examples=["Middle Office"])
    description: str = Field(examples=[TRADE_CONFIRMATIONS_CREATE["description"]])
    tags: list[str] = Field(
        max_length=MAX_TAGS,
        examples=[["trading", "finance", "settlements", "daily"]],
    )
    summary: str = Field(
        examples=["A daily export of confirmed trades covering counterparties and settlements."],
    )
    curation_status: Literal["ok", "partial", "failed"] = Field(
        default="ok",
        examples=["ok"],
        description=(
            "ok when Jev and Llama both succeeded. "
            "partial when exactly one succeeded. "
            "failed when both failed (empty tags and a placeholder summary)."
        ),
    )


class FieldError(BaseModel):
    """One invalid request field."""

    model_config = ConfigDict(title="FieldError")

    field: str = Field(examples=["name"])
    message: str = Field(examples=["name is required"])


class ValidationErrorResponse(BaseModel):
    """400 body. `error` stays a string; `fields` names each invalid input."""

    model_config = ConfigDict(
        title="ValidationErrorResponse",
        json_schema_extra={"examples": [VALIDATION_ERROR_EXAMPLE]},
    )

    error: str = Field(examples=["Validation failed"])
    fields: list[FieldError]


class ErrorResponse(BaseModel):
    """Non-validation error body, e.g. 404. Always includes `{ \"error\": \"...\" }`."""

    model_config = ConfigDict(
        title="ErrorResponse",
        json_schema_extra={"examples": [NOT_FOUND_ERROR_EXAMPLE]},
    )

    error: str = Field(examples=["Dataset with id 'missing' was not found."])
