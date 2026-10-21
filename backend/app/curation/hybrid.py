from app.curation.base import Curator
from app.curation.classifier import ClassifierCurator
from app.curation.llm import LlmCurator
from app.schemas import CurationResult, DatasetCreate


class HybridCurator(Curator):
    """Jev picks tags. Llama writes the summary."""

    def __init__(self, classifier: ClassifierCurator, summarizer: LlmCurator) -> None:
        self.classifier = classifier
        self.summarizer = summarizer

    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        tags = self.classifier.classify(payload, dataset_id=dataset_id)
        summary = self.summarizer.summarise(payload, tags, dataset_id=dataset_id)
        return CurationResult(tags=tags, summary=summary)
