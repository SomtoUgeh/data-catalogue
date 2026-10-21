from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.curation.base import Curator
from app.curation.factory import get_curator
from app.repositories.dataset_repository import DatasetRepository
from app.routers.datasets import router as datasets_router
from app.schemas import ErrorResponse
from app.services.dataset_service import DatasetNotFoundError, DatasetService


def _validation_message(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        field = next((str(loc) for loc in reversed(err["loc"]) if loc != "body"), "")
        msg = err.get("msg", "is invalid")
        if msg.startswith("Value error, "):
            msg = msg.removeprefix("Value error, ")
        if err.get("type") == "missing" and field:
            parts.append(f"{field} is required")
        elif field and not msg.startswith(field):
            parts.append(f"{field} {msg}")
        else:
            parts.append(msg)
    return "; ".join(parts) or "Invalid request body."


def create_app(
    repository: DatasetRepository | None = None,
    curator: Curator | None = None,
) -> FastAPI:
    app = FastAPI(title="Data Catalogue", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    repo = repository or DatasetRepository()
    app.state.repository = repo
    app.state.service = DatasetService(repo, curator or get_curator())
    app.include_router(datasets_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error=_validation_message(exc)).model_dump(),
        )

    @app.exception_handler(DatasetNotFoundError)
    async def not_found_handler(_request, exc: DatasetNotFoundError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error=str(exc)).model_dump(),
        )

    return app


app = create_app()
