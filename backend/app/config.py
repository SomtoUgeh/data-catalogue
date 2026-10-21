from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_LLM_MODEL = "workers-ai/@cf/meta/llama-3.3-70b-instruct-fp8-fast"
DEFAULT_CLASSIFIER_MODEL = "typesafe/jev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cf_account_id: str = ""
    cf_ai_gateway_id: str = ""
    cf_ai_gateway_token: str = ""
    llm_provider_api_key: str = ""
    llm_model: str = DEFAULT_LLM_MODEL
    classifier_model: str = DEFAULT_CLASSIFIER_MODEL
    request_timeout_seconds: float = 8.0

    @property
    def llm_ready(self) -> bool:
        return bool(
            self.cf_account_id.strip()
            and self.cf_ai_gateway_id.strip()
            and self.llm_provider_api_key.strip()
        )

    @property
    def gateway_base_url(self) -> str:
        return (
            "https://gateway.ai.cloudflare.com/v1/"
            f"{self.cf_account_id.strip()}/{self.cf_ai_gateway_id.strip()}/compat"
        )

    @property
    def classifier_run_url(self) -> str:
        return f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id.strip()}/ai/run"


@lru_cache
def get_settings() -> Settings:
    return Settings()
