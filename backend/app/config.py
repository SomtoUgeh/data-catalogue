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

    @property
    def workers_ai_ready(self) -> bool:
        return bool(self.cf_account_id.strip() and self.llm_provider_api_key.strip())

    @property
    def workers_ai_chat_url(self) -> str:
        return (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.cf_account_id.strip()}/ai/v1/chat/completions"
        )

    def workers_ai_model(self) -> str:
        model = self.llm_model.strip()
        return model.removeprefix("workers-ai/")


def settings_from_env(env: object) -> Settings:
    def read(name: str, default: str = "") -> str:
        value = getattr(env, name, None)
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    return Settings(
        cf_account_id=read("CF_ACCOUNT_ID"),
        cf_ai_gateway_id=read("CF_AI_GATEWAY_ID"),
        cf_ai_gateway_token=read("CF_AI_GATEWAY_TOKEN"),
        llm_provider_api_key=read("LLM_PROVIDER_API_KEY"),
        llm_model=read("LLM_MODEL", DEFAULT_LLM_MODEL),
        classifier_model=read("CLASSIFIER_MODEL", DEFAULT_CLASSIFIER_MODEL),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
