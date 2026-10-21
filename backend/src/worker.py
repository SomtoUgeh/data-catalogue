"""Cloudflare Worker entry point. Serves the FastAPI app with D1 storage and Workers AI curation.

Bindings (DB, AI, WRITE_LIMITER) and vars (CLASSIFIER_MODEL, SUMMARY_MODEL, AI_GATEWAY_ID) come from
wrangler.jsonc and arrive on each request as `env`.
"""

import logging

import js  # pyright: ignore[reportMissingImports]  # provided by the Python Workers runtime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send
from workers import asgi

from app.api.dependencies import get_service
from app.curation.workers_ai import WorkersAiCurator
from app.logs import configure_logging
from app.main import create_app
from app.repositories.d1 import D1DatasetStore
from app.schemas import ErrorResponse
from app.services.datasets import DatasetService

WRITE_METHODS = {"POST", "DELETE"}
WRITE_LIMIT_PERIOD_SECONDS = 60  # matches "period" of WRITE_LIMITER in wrangler.jsonc


def service_from_env(request: Request) -> DatasetService:
    env = request.scope["env"]
    curator = WorkersAiCurator(env.AI, env.CLASSIFIER_MODEL, env.SUMMARY_MODEL, gateway_id=env.AI_GATEWAY_ID)
    return DatasetService(D1DatasetStore(env.DB), curator)


class WriteRateLimit:
    """Limits writes per client IP, because the API has no sign-in and each create runs two AI calls.

    This is plain ASGI middleware. Starlette's BaseHTTPMiddleware (@app.middleware) runs the app in a
    separate task, and that raises proxy errors in the Python Workers runtime.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in WRITE_METHODS:
            client_ip = Headers(scope=scope).get("cf-connecting-ip", "unknown")
            outcome = await scope["env"].WRITE_LIMITER.limit({"key": client_ip})
            if not outcome["success"]:
                body = ErrorResponse(error="Too many requests. Try again in a minute.")
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=body.model_dump(),
                    headers={"Retry-After": str(WRITE_LIMIT_PERIOD_SECONDS)},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


class ConsoleLogHandler(logging.Handler):
    """Writes each record to the JS console as an object, at the matching console level.

    Workers Logs indexes the fields of a logged object, so events from app/logs.py become searchable by
    field (for example outcome or curation_id), and warnings and errors keep their level.
    """

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        try:
            entry = js.JSON.parse(message)
        except Exception:  # a plain-text record from a library
            entry = message
        if record.levelno >= logging.ERROR:
            js.console.error(entry)
        elif record.levelno >= logging.WARNING:
            js.console.warn(entry)
        else:
            js.console.log(entry)


configure_logging(ConsoleLogHandler())
app = create_app()
app.dependency_overrides[get_service] = service_from_env
app.add_middleware(WriteRateLimit)

Default = asgi.entrypoint(app)
