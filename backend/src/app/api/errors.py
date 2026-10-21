"""Exception handlers. Every error response has the same shape: {"error": str}, plus "fields" on a 400."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails

from app.schemas import ErrorResponse, FieldError, ValidationErrorResponse
from app.services.datasets import DatasetNotFoundError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.exception_handler(RequestValidationError)(validation_error)
    app.exception_handler(DatasetNotFoundError)(dataset_not_found)
    app.exception_handler(Exception)(unexpected_error)


async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Returns 400 (FastAPI's default is 422) and names each invalid field."""
    body = ValidationErrorResponse(error="Validation failed", fields=[_field_error(e) for e in exc.errors()])
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


async def dataset_not_found(_request: Request, exc: DatasetNotFoundError) -> JSONResponse:
    body = ErrorResponse(error=f"Dataset '{exc.dataset_id}' not found")
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=body.model_dump())


async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Logs the traceback and hides the details from the client."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    body = ErrorResponse(error="Internal server error")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())


def _field_error(error: ErrorDetails) -> FieldError:
    # loc is ("body", "<field>") for a field error, and ("body", <offset>) for malformed JSON.
    field = error["loc"][-1] if isinstance(error["loc"][-1], str) else "body"
    match error["type"]:
        case "missing" | "string_too_short":
            message = f"{field} is required"
        case "string_too_long":
            limit = (error.get("ctx") or {}).get("max_length")
            message = f"{field} must be at most {limit} characters"
        case _:
            message = error["msg"]
    return FieldError(field=field, message=message)
