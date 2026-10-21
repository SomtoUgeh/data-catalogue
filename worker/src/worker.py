import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from fastapi import Request
from fastapi.responses import Response
from workers import asgi

from app.config import settings_from_env
from app.curation.base import Curator
from app.curation.factory import get_worker_curator
from app.curation.outcome import CurationFailed, CurationOutcome
from app.main import create_app
from app.repositories.d1_dataset_repository import D1DatasetRepository
from app.schemas import DatasetCreate
from app.services.dataset_service import DatasetService


class UnboundCurator(Curator):
    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationOutcome:
        return CurationFailed()


app = create_app(curator=UnboundCurator())


@app.middleware("http")
async def bind_worker_state(request: Request, call_next):
    env = request.scope.get("env")
    if env is not None and getattr(env, "DB", None) is not None:
        settings = settings_from_env(env)
        request.state.service = DatasetService(
            D1DatasetRepository(env.DB),
            get_worker_curator(settings, ai_binding=getattr(env, "AI", None)),
        )
    return await call_next(request)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.get("/__worker_probe", include_in_schema=False)
async def worker_probe() -> dict[str, str]:
    report: dict[str, str] = {}
    for name in (
        "fastapi",
        "pydantic",
        "httpx",
        "httpx2",
        "pydantic_ai",
        "pydantic_ai.models.openai",
    ):
        try:
            __import__(name)
            report[name] = "ok"
        except Exception as exc:
            report[name] = f"{type(exc).__name__}"
    return report


def _asset_headers(resp) -> dict[str, str]:
    headers: dict[str, str] = {}
    raw = getattr(resp, "headers", None)
    if raw is None:
        return headers
    try:
        for key in raw:
            headers[str(key)] = str(raw.get(key))
    except Exception:
        content_type = None
        try:
            content_type = raw.get("content-type")
        except Exception:
            content_type = None
        if content_type:
            headers["content-type"] = str(content_type)
    headers.pop("content-encoding", None)
    headers.pop("content-length", None)
    return headers


@app.get("/{path:path}", include_in_schema=False)
async def frontend(path: str, request: Request) -> Response:
    env = request.scope["env"]
    asset_path = path if path else "index.html"
    resp = await env.ASSETS.fetch(f"https://assets.local/{asset_path}")
    last_segment = path.rsplit("/", 1)[-1]
    if resp.status == 404 and "." not in last_segment:
        resp = await env.ASSETS.fetch("https://assets.local/index.html")
    body = await resp.bytes()
    return Response(content=bytes(body), status_code=resp.status, headers=_asset_headers(resp))


Default = asgi.entrypoint(app)
