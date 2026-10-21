from app.config import Settings, get_settings
from app.curation.base import CurationError, Curator
from app.curation.keyword import KeywordCurator
from app.curation.llm import LlmCurator
from app.schemas import CurationResult, DatasetCreate


class FailingCurator(Curator):
    """Used with CURATOR=fail to demonstrate the UI fallback notice."""

    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        raise CurationError("forced curator failure")


def get_curator(settings: Settings | None = None) -> Curator:
    """Keyword mock is the default. Gateway id + provider key opts into the LLM."""
    resolved = settings or get_settings()
    mode = resolved.curator.strip().lower()
    if mode == "fail":
        return FailingCurator()
    if mode == "mock":
        return KeywordCurator()
    if mode == "llm" or resolved.llm_ready:
        if resolved.llm_ready:
            return LlmCurator(resolved)
        return KeywordCurator()
    return KeywordCurator()
