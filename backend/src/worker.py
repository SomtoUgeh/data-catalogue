"""Cloudflare Worker entry point. Serves the FastAPI app with D1 storage and Workers AI curation.

Bindings (DB, AI) and vars (CLASSIFIER_MODEL, SUMMARY_MODEL) come from wrangler.jsonc and arrive on each
request as `env`.
"""

from fastapi import Request
from workers import asgi

from app.curation.workers_ai import WorkersAiCurator
from app.main import create_app
from app.repositories.d1 import D1DatasetStore
from app.routers.datasets import get_service
from app.services.dataset_service import DatasetService

app = create_app()


def service_from_env(request: Request) -> DatasetService:
    env = request.scope["env"]
    curator = WorkersAiCurator(env.AI, env.CLASSIFIER_MODEL, env.SUMMARY_MODEL)
    return DatasetService(D1DatasetStore(env.DB), curator)


app.dependency_overrides[get_service] = service_from_env

Default = asgi.entrypoint(app)
