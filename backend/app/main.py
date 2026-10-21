import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.curation.base import Curator
from app.curation.factory import get_curator
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.store import DatasetStore
from app.routers.datasets import router as datasets_router
from app.schemas import ErrorResponse, FieldError, ValidationErrorResponse
from app.services.dataset_service import DatasetNotFoundError, DatasetService

logger = logging.getLogger("uvicorn.error")


def _field_message(err: dict) -> str:
    field = next((str(loc) for loc in reversed(err["loc"]) if loc != "body"), "")
    msg = err.get("msg", "is invalid")
    if msg.startswith("Value error, "):
        msg = msg.removeprefix("Value error, ")
    err_type = err.get("type")
    if field and err_type in {"missing", "string_too_short", "string_type"}:
        return f"{field} is required"
    if field and not msg.startswith(field):
        return f"{field} {msg}"
    return msg


def _validation_fields(exc: RequestValidationError) -> list[FieldError]:
    fields: list[FieldError] = []
    for err in exc.errors():
        field = next((str(loc) for loc in reversed(err["loc"]) if loc != "body"), "")
        if not field:
            continue
        fields.append(FieldError(field=field, message=_field_message(err)))
    return fields


def create_app(
    repository: DatasetStore | None = None,
    curator: Curator | None = None,
) -> FastAPI:
    repo = repository or DatasetRepository()
    resolved_curator = curator or get_curator()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logger.info("curator=%s", type(resolved_curator).__name__)
        yield

    app = FastAPI(
        title="Data Catalogue",
        version="1.0.0",
        description=(
            "Register datasets, attach curator tags and a one-sentence summary, "
            "then list or delete them. Validation failures are 400 with "
            '`{ "error": "Validation failed", "fields": [...] }`, '
            "not FastAPI's default 422."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.repository = repo
    app.state.service = DatasetService(repo, resolved_curator)
    app.include_router(datasets_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content=ValidationErrorResponse(
                error="Validation failed",
                fields=_validation_fields(exc),
            ).model_dump(),
        )

    @app.exception_handler(DatasetNotFoundError)
    async def not_found_handler(_request, exc: DatasetNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error=str(exc)).model_dump(),
        )

    return app


app = create_app()
