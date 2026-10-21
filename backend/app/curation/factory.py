from app.config import Settings, get_settings
from app.curation.base import Curator
from app.curation.keyword import KeywordCurator
from app.curation.llm import LlmCurator


def get_curator(settings: Settings | None = None) -> Curator:
    """Keyword mock is the default. Gateway id + provider key opts into the LLM."""
    resolved = settings or get_settings()
    mode = resolved.curator.strip().lower()
    if mode == "mock":
        return KeywordCurator()
    if mode == "llm" or resolved.llm_ready:
        if resolved.llm_ready:
            return LlmCurator(resolved)
        return KeywordCurator()
    return KeywordCurator()
