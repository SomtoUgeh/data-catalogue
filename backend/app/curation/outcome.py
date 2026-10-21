from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field

PLACEHOLDER_SUMMARY = (
    "Curation unavailable. Tags and summary will appear once tagging succeeds."
)


class CurationOk(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
    tags: list[str]
    summary: str


class CurationPartial(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["partial"] = "partial"
    tags: list[str]
    summary: str


class CurationFailed(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["failed"] = "failed"
    tags: list[str] = Field(default_factory=list)
    summary: str = PLACEHOLDER_SUMMARY


CurationOutcome = Annotated[
    CurationOk | CurationPartial | CurationFailed,
    Discriminator("status"),
]


def compose_curation(tags: list[str] | None, summary: str | None) -> CurationOutcome:
    if tags and summary:
        return CurationOk(tags=tags, summary=summary)
    if tags:
        return CurationPartial(tags=tags, summary=PLACEHOLDER_SUMMARY)
    if summary:
        return CurationPartial(tags=[], summary=summary)
    return CurationFailed()
