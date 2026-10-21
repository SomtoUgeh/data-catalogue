from fastapi import FastAPI

from app.api.datasets import router as datasets_router
from app.api.errors import register_exception_handlers
from app.curation.keyword import KeywordCurator
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.services.datasets import DatasetService


def create_app(service: DatasetService | None = None) -> FastAPI:
    """Builds the API around a DatasetService.

    `app` below wires the local setup (in-memory store, keyword curator). On Cloudflare, worker.py
    binds a service per request from the Worker environment instead (D1 store, Workers AI curator).
    """
    app = FastAPI(title="Data Catalogue API", version="1.0.0")
    app.state.dataset_service = service
    app.include_router(datasets_router)
    register_exception_handlers(app)
    return app


app = create_app(DatasetService(InMemoryDatasetStore(SEED_DATASETS), KeywordCurator()))
