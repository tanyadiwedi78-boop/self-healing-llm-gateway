import logging
from functools import lru_cache
from pydantic import SecretStr

from app.core.config import get_settings
from app.providers.models import Provider

logger = logging.getLogger(__name__)


@lru_cache
def get_providers() -> list[Provider]:
    # Build the provider list once from config, then reuse it
    settings = get_settings()
    providers = []

    for name in settings.provider_names:
        # Config must have <name>_api_key and <name>_model (for example groq_api_key)
        api_key = getattr(settings, f"{name}_api_key")
        model = getattr(settings, f"{name}_model")

        has_key = bool(api_key.get_secret_value())
        has_model = bool(model.strip())
        enabled = has_key and has_model

        if not has_key:
            logger.warning(f"provider_disabled name={name} reason=missing_api_key")
        elif not has_model:
            logger.warning(f"provider_disabled name={name} reason=missing_model")
        

        # A provider without a key is disabled, not a crash
        enabled = bool(api_key.get_secret_value())
        if not enabled:
            logger.warning(f"provider_disabled name={name} reason=missing_api_key")

        providers.append(
            Provider(
                name=name,
                model=model,
                api_key=api_key,
                timeout_seconds=settings.provider_timeout_seconds,
                enabled=enabled,
            )
        )

            # Optional fake provider for tests and demos (config blocks it in production)
        if settings.enable_mock_provider:
                providers.append(
                    Provider(
                        name="mock",
                        model="mock/default",
                        api_key=SecretStr("mock"),
                        timeout_seconds=settings.provider_timeout_seconds,
                    )
                )
        
    return providers


def get_enabled_providers() -> list[Provider]:
    # Only providers that have a key
    return [p for p in get_providers() if p.enabled]


def get_provider(name: str) -> Provider | None:
    # Find one provider by name, or None if it does not exist
    for provider in get_providers():
        if provider.name == name:
            return provider
    return None


def check_providers_ready() -> None:
    # Called once at startup (main.py). Stop early if nothing can answer.
    enabled = get_enabled_providers()
    if not enabled:
        raise RuntimeError("No LLM provider is enabled. Set at least one API key in .env")
    names = [p.name for p in enabled]
    logger.info(f"providers_ready enabled={names}")