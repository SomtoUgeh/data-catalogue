from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails

from app.curation.keyword import KeywordCurator
from app.repositories.memory import InMemoryDatasetStore
from app.repositories.seed import SEED_DATASETS
from app.routers.datasets import router as datasets_router
from app.schemas import ErrorResponse, FieldError, ValidationErrorResponse
from app.services.dataset_service import DatasetNotFoundError, DatasetService


def create_app(service: DatasetService | None = None) -> FastAPI:
    """Builds the API around a DatasetService.

    `app` below wires the local setup (in-memory store, keyword curator). On Cloudflare, worker.py
    binds a service per request from the Worker environment instead (D1 store, Workers AI curator).
    """
    app = FastAPI(title="Data Catalogue API", version="1.0.0")
    app.state.dataset_service = service
    app.include_router(datasets_router)
    app.exception_handler(RequestValidationError)(validation_error_handler)
    app.exception_handler(DatasetNotFoundError)(not_found_handler)
    return app


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Returns 400 (FastAPI's default is 422) and names each invalid field."""
    body = ValidationErrorResponse(error="Validation failed", fields=[_field_error(e) for e in exc.errors()])
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


async def not_found_handler(_request: Request, exc: DatasetNotFoundError) -> JSONResponse:
    body = ErrorResponse(error=f"Dataset '{exc}' not found")
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=body.model_dump())


def _field_error(error: ErrorDetails) -> FieldError:
    # The last location element is the field name, or a character offset for a JSON syntax error.
    field = str(error["loc"][-1])
    if error["type"] in ("missing", "string_too_short"):
        return FieldError(field=field, message=f"{field} is required")
    return FieldError(field=field, message=error["msg"])


app = create_app(DatasetService(InMemoryDatasetStore(SEED_DATASETS), KeywordCurator()))
