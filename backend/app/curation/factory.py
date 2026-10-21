from app.config import Settings, get_settings
from app.curation.base import Curator
from app.curation.classifier import ClassifierCurator
from app.curation.hybrid import HybridCurator
from app.curation.keyword import KeywordCurator
from app.curation.llm import LlmCurator


def get_curator(settings: Settings | None = None) -> Curator:
    """Keyword mock is the default. A live key opts into Jev tags + LLM summary."""
    resolved = settings or get_settings()
    mode = resolved.curator.strip().lower()
    if mode == "mock":
        return KeywordCurator()
    if mode == "llm":
        return LlmCurator(resolved) if resolved.llm_ready else KeywordCurator()
    if mode == "classifier":
        return ClassifierCurator(resolved) if resolved.llm_ready else KeywordCurator()
    if resolved.llm_ready:
        return HybridCurator(
            ClassifierCurator(resolved),
            LlmCurator(resolved),
            KeywordCurator(),
        )
    return KeywordCurator()
