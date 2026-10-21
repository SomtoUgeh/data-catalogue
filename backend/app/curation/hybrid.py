from app.curation.base import Curator
from app.curation.classifier import ClassifierCurator
from app.curation.llm import LlmCurator
from app.curation.outcome import CurationOutcome, compose_curation
from app.schemas import DatasetCreate


class HybridCurator(Curator):
    """Jev picks tags. Llama writes the summary. Each side can fail on its own."""

    def __init__(self, classifier: ClassifierCurator, summarizer: LlmCurator) -> None:
        self.classifier = classifier
        self.summarizer = summarizer

    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationOutcome:
        tags: list[str] | None
        try:
            tags = self.classifier.classify(payload, dataset_id=dataset_id)
        except Exception:
            tags = None

        summary: str | None
        try:
            summary = self.summarizer.summarise(payload, tags or [], dataset_id=dataset_id)
        except Exception:
            summary = None

        return compose_curation(tags, summary)
