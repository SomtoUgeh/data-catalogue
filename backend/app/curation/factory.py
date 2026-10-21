from app.config import Settings, get_settings
from app.curation.classifier import ClassifierCurator
from app.curation.hybrid import HybridCurator


def get_curator(settings: Settings | None = None) -> HybridCurator:
    from app.curation.llm import LlmCurator

    resolved = settings or get_settings()
    return HybridCurator(ClassifierCurator(resolved), LlmCurator(resolved))


def get_worker_curator(settings: Settings | None = None, ai_binding=None) -> HybridCurator:
    from app.curation.http_llm import HttpLlmCurator

    resolved = settings or get_settings()
    return HybridCurator(
        ClassifierCurator(resolved, ai_binding=ai_binding),
        HttpLlmCurator(resolved, ai_binding=ai_binding),
    )
