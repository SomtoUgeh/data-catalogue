import json

import httpx2
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import Settings
from app.curation.base import CurationError
from app.schemas import DatasetCreate, SummaryResult

SUMMARY_INSTRUCTIONS = """You write one catalogue summary sentence.

Return a JSON object that matches the provided schema.

Rules:
- one sentence, under 25 words, starts with "A "
- derive it from the name, description, and tags
- do not invent tags or change the tags you were given

Examples:
name: Customer Transactions
description: Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.
tags: finance, transactions, PII, daily
{"summary": "A daily feed of customer transaction records covering amounts, currencies, and timestamps."}

name: Product Inventory
description: Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.
tags: inventory, operations, warehouse
{"summary": "A warehouse snapshot tracking stock levels and reorder thresholds per product SKU."}
"""


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
        if self._model is None and not self.settings.llm_ready:
            raise CurationError("Cloudflare AI Gateway is not configured")

        prompt = (
            f"name: {payload.name}\n"
            f"description: {payload.description}\n"
            f"tags: {', '.join(tags)}\n"
            "Write only the one-sentence summary. Do not change the tags."
        )
        result = self._summary_agent(dataset_id).run_sync(prompt)
        return result.output.summary

    def _summary_agent(self, dataset_id: str) -> Agent[None, SummaryResult]:
        model = self._model or self._gateway_model(dataset_id)
        return Agent(
            model,
            output_type=PromptedOutput(SummaryResult),
            instructions=SUMMARY_INSTRUCTIONS,
            retries={"output": 2},
        )

    def _gateway_model(self, dataset_id: str) -> OpenAIChatModel:
        headers = {
            "cf-aig-metadata": json.dumps({"dataset_id": dataset_id or "pending"}),
        }
        if self.settings.cf_ai_gateway_token.strip():
            headers["cf-aig-authorization"] = (
                f"Bearer {self.settings.cf_ai_gateway_token.strip()}"
            )

        http_client = self._http_client or httpx2.AsyncClient(
            headers=headers,
            timeout=self.settings.request_timeout_seconds,
        )
        return OpenAIChatModel(
            self.settings.llm_model,
            provider=OpenAIProvider(
                base_url=self.settings.gateway_base_url,
                api_key=self.settings.llm_provider_api_key,
                http_client=http_client,
            ),
        )
