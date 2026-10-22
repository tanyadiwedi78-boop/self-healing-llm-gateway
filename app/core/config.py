from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------- App ----------
    app_name: str = "Self Healing LLM Gateway"
    app_version: str = "0.1.0"
    environment: str = "development"   # development | production
    debug: bool = False
    api_prefix: str = "/v1"

    gateway_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API key clients must send to access the gateway",
    )

    tenants_file: str = Field(
        default="tenants.json",
        description="JSON file that maps hashed API keys to tenants",
    )

    # ---------- LLM provider keys ----------
    groq_api_key: SecretStr = Field(default=SecretStr(""))
    gemini_api_key: SecretStr = Field(default=SecretStr(""))


    pricing_file : str = "pricing.json"

    #------------   Providers Name ------------------
    provider_names: list[str] = ["gemini", "groq"]

    enable_mock_provider: bool = False

    #----------- logging ----------------------------
    log_json: bool = Field(
        default=False,
        description = "true = JSON log lines , false = readable text"
    )

    log_level: str = Field(
        default = "INFO" , 
        description = "DEBUG , INFO , WARNING , ERROR"
    )


    # ---------- Request limits (guardrails) ----------
    max_messages: int = 50              # most messages allowed in one request
    max_request_chars: int = 50_000     # most total characters allowed in one request

    # ---------- Safety switches ----------
    enable_docs: bool = True            # /docs page; must be False in production
    enable_chaos: bool = False          # chaos switch; must be False in production


    

    # ---------- Default models (LiteLLM format: "provider/model") ----------
    groq_model: str = "groq/qwen/qwen3.8-27b"
    gemini_model: str = "gemini/gemini-3.1-flash-lite"

    provider_timeout_seconds: float = Field(
        default=20.0,
        description="Maximum time for one provider call before ProviderTimeoutError",
    )

    # ---------- Redis ----------
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis for sliding windows, health metrics, and the queue",
    )

    # ---------- Health tracking ----------
    health_window_seconds: int = Field(
        default=60,
        description="Only the last N seconds of data count toward provider health",
    )
    health_min_samples: int = Field(
        default=10,
        description="With fewer requests than this, error rate alone cannot trip the breaker",
    )
    error_rate_threshold: float = Field(
        default=0.30,
        description="Error rate above this within the window marks a provider unhealthy",
    )
    p95_latency_threshold_ms: int = Field(
        default=3000,
        description="p95 latency above this marks a provider as degraded",
    )

    # ---------- Circuit breaker ----------
    circuit_failure_threshold: int = Field(
        default=5,
        description="Consecutive failures that move the breaker from closed to open",
    )
    circuit_recovery_timeout_seconds: int = Field(
        default=30,
        description="Time spent in the open state before a half-open probe is allowed",
    )
    circuit_half_open_max_calls: int = Field(
        default=1,
        description="Number of probe calls allowed while half-open",
    )

    max_output_tokens: int = Field(
        default=1024,
        description="Upper limit for max_tokens on every request (protects cost)",
    )

    # ---------- Retry ----------
    max_retries: int = Field(
        default=2,
        description="Maximum retries before falling back to the next provider",
    )
    retry_base_delay_seconds: float = Field(
        default=1.0,
        description="Base delay for exponential backoff with jitter",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _require_gateway_key_in_production(self) -> "Settings":
        if self.environment == "production" and not self.gateway_api_key.get_secret_value():
            raise ValueError("GATEWAY_API_KEY must be set when environment is 'production'")
        return self

    
    @model_validator(mode="after")
    def _no_mock_in_production(self) -> "Settings":

        if self.environment == "production" and self.enable_mock_provider:
            raise ValueError("ENABLE_MOCK_PROVIDER must be false in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()