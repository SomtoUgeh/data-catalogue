from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails

from app.curation.keyword import KeywordCurator
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.routers.datasets import router as datasets_router
from app.services.dataset_service import DatasetService


def create_app(service: DatasetService | None = None) -> FastAPI:
    """Builds the API around a DatasetService.

    `app` below wires the local setup (in-memory store, keyword curator). On Cloudflare, worker.py
    binds a service per request from the Worker environment instead (D1 store, Workers AI curator).
    """
    app = FastAPI(title="Data Catalogue API")
    app.state.dataset_service = service
    app.include_router(datasets_router)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    return app


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Returns 400 (FastAPI's default is 422) with the same {"detail": str} shape as other errors."""
    message = "; ".join(_describe(error) for error in exc.errors())
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": message})


def _describe(error: ErrorDetails) -> str:
    field = error["loc"][-1]
    if error["type"] in ("missing", "string_too_short"):
        return f"{field} is required"
    # A JSON syntax error is located by character offset, not by field name.
    return f"{field}: {error['msg']}" if isinstance(field, str) else error["msg"]


app = create_app(DatasetService(InMemoryDatasetStore(SEED_DATASETS), KeywordCurator()))
