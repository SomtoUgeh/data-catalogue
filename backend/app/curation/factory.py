from app.config import Settings, get_settings
from app.curation.classifier import ClassifierCurator
from app.curation.hybrid import HybridCurator
from app.curation.llm import LlmCurator


def get_curator(settings: Settings | None = None) -> HybridCurator:
    resolved = settings or get_settings()
    return HybridCurator(ClassifierCurator(resolved), LlmCurator(resolved))
