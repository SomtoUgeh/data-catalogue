import json
from typing import Any

import httpx

from app.config import Settings
from app.curation.base import CurationError
from app.curation.summary import SUMMARY_INSTRUCTIONS, parse_summary, summary_user_prompt
from app.runtime import unwrap
from app.schemas import DatasetCreate

_ATTEMPTS = 3


def _message_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("response"), str):
            return payload["response"]
        if isinstance(payload.get("result"), str):
            return payload["result"]
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        result = payload.get("result")
        if isinstance(result, dict):
            return _message_text(result)
    response = getattr(payload, "response", None)
    if isinstance(response, str):
        return response
    return str(payload)


class HttpLlmCurator:
    """Chat completions + Pydantic SummaryResult. Used when pydantic-ai cannot run."""

    def __init__(self, settings: Settings, http_client=None, ai_binding=None) -> None:
        self.settings = settings
        self._http_client = http_client
        self._ai = ai_binding

    def summarise(self, payload: DatasetCreate, tags: list[str], dataset_id: str = "") -> str:
        if self._ai is None and not self.settings.llm_ready and not self.settings.workers_ai_ready:
            raise CurationError("Cloudflare Workers AI is not configured")

        prompt = summary_user_prompt(payload, tags)
        last_error: Exception | None = None
        for _ in range(_ATTEMPTS):
            try:
                raw = self._complete(prompt, dataset_id)
                return parse_summary(raw)
            except CurationError as exc:
                last_error = exc
            except Exception as exc:
                last_error = CurationError(f"summary failed: {type(exc).__name__}")
        raise CurationError("summary failed validation") from last_error

    def _complete(self, prompt: str, dataset_id: str) -> str:
        messages = [
            {"role": "system", "content": SUMMARY_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ]
        if self._ai is not None:
            result = unwrap(
                self._ai.run(
                    self.settings.workers_ai_model(),
                    {"messages": messages},
                )
            )
            return _message_text(result)

        headers = {
            "Authorization": f"Bearer {self.settings.llm_provider_api_key}",
            "Content-Type": "application/json",
            "cf-aig-metadata": json.dumps(
                {"dataset_id": dataset_id or "pending", "role": "summary"}
            ),
        }
        if self.settings.cf_ai_gateway_token.strip():
            headers["cf-aig-authorization"] = f"Bearer {self.settings.cf_ai_gateway_token.strip()}"

        url = (
            f"{self.settings.gateway_base_url}/chat/completions"
            if self.settings.llm_ready
            else self.settings.workers_ai_chat_url
        )
        model = (
            self.settings.llm_model if self.settings.llm_ready else self.settings.workers_ai_model()
        )
        body = {"model": model, "messages": messages}

        client = self._http_client or httpx.Client(timeout=self.settings.request_timeout_seconds)
        close_client = self._http_client is None
        try:
            response = client.post(url, json=body, headers=headers)
            if response.status_code >= 400:
                raise CurationError(f"summary HTTP {response.status_code}")
            return _message_text(response.json())
        finally:
            if close_client:
                client.close()
