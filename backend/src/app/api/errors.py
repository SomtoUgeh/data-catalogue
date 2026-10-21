"""Exception handlers. Every error response has the same shape: {"error": str}, plus "fields" on a 400."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails
from starlette.exceptions import HTTPException

from app.logs import current_traceback, log_event
from app.schemas import ErrorResponse, FieldError, ValidationErrorResponse
from app.services.datasets import DatasetNotFoundError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.exception_handler(RequestValidationError)(validation_error)
    app.exception_handler(DatasetNotFoundError)(dataset_not_found)
    app.exception_handler(HTTPException)(http_error)
    app.exception_handler(Exception)(unexpected_error)


async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Returns 400 (FastAPI's default is 422) and names each invalid field."""
    body = ValidationErrorResponse(error="Validation failed", fields=[_field_error(e) for e in exc.errors()])
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


async def dataset_not_found(_request: Request, exc: DatasetNotFoundError) -> JSONResponse:
    body = ErrorResponse(error=f"Dataset '{exc.dataset_id}' not found")
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=body.model_dump())


async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    """Errors raised by routing, such as an unknown path (404) or a wrong method (405)."""
    body = ErrorResponse(error=exc.detail)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(), headers=exc.headers)


async def unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
    """Logs the traceback and hides the details from the client."""
    log_event(
        logger,
        logging.ERROR,
        "unhandled_error",
        method=request.method,
        path=request.url.path,
        traceback=current_traceback(),
    )
    body = ErrorResponse(error="Internal server error")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())


def _field_error(error: ErrorDetails) -> FieldError:
    # loc is ("body", "<field>") or ("query", "<param>") for one value, and ("body",) or ("body", <offset>)
    # when the body as a whole is missing, malformed, or not an object.
    loc = error["loc"]
    if len(loc) < 2 or not isinstance(loc[-1], str):
        return FieldError(field="body", message="Request body must be a JSON object")

    field = loc[-1]
    label = field.capitalize()
    match error["type"]:
        case "missing" | "string_too_short":
            message = f"{label} is required"
        case "string_too_long":
            limit = (error.get("ctx") or {}).get("max_length")
            message = f"{label} must be at most {limit} characters"
        case "string_pattern_mismatch":
            message = f"{label} must be a dataset id"
        case _:
            message = f"{label}: {error['msg']}"
    return FieldError(field=field, message=message)
