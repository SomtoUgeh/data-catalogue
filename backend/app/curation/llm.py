from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.config import Settings
from app.curation.base import CurationError
from app.curation.summary import SUMMARY_INSTRUCTIONS, summary_user_prompt
from app.schemas import DatasetCreate

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_ai.models import Model
    from pydantic_ai.models.openai import OpenAIChatModel

    from app.schemas import SummaryResult


class LlmCurator:
    def __init__(
        self,
        settings: Settings,
        model: Model | None = None,
        http_client=None,
    ) -> None:
        self.settings = settings
        self._model = model
        self._http_client = http_client

    def summarise(self, payload: DatasetCreate, tags: list[str], dataset_id: str = "") -> str:
        if self._model is None and not (self.settings.llm_ready or self.settings.workers_ai_ready):
            raise CurationError("Cloudflare Workers AI is not configured")

        result = self._summary_agent(dataset_id).run_sync(summary_user_prompt(payload, tags))
        return result.output.summary

    def _summary_agent(self, dataset_id: str) -> Agent[None, SummaryResult]:
        import os

        os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
        from pydantic_ai import Agent, PromptedOutput

        from app.schemas import SummaryResult

        model = self._model or self._openai_model(dataset_id)
        return Agent(
            model,
            output_type=PromptedOutput(SummaryResult),
            instructions=SUMMARY_INSTRUCTIONS,
            retries={"output": 2},
        )

    def _openai_model(self, dataset_id: str) -> OpenAIChatModel:
        import httpx2
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        headers = {
            "cf-aig-metadata": json.dumps({"dataset_id": dataset_id or "pending"}),
        }
        if self.settings.cf_ai_gateway_token.strip():
            headers["cf-aig-authorization"] = f"Bearer {self.settings.cf_ai_gateway_token.strip()}"

        if self.settings.llm_ready:
            base_url = self.settings.gateway_base_url
            model_name = self.settings.llm_model
        else:
            base_url = self.settings.workers_ai_base_url
            model_name = self.settings.workers_ai_model()

        http_client = self._http_client or httpx2.AsyncClient(
            headers=headers,
            timeout=self.settings.request_timeout_seconds,
        )
        return OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(
                base_url=base_url,
                api_key=self.settings.llm_provider_api_key,
                http_client=http_client,
            ),
        )
