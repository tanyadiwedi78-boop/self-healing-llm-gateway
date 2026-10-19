import logging
import time

import litellm

from app.core import exceptions as errors
from app.providers.models import CallResult, Provider
from app.schemas.requests import ChatRequest

logger = logging.getLogger(__name__)


litellm.drop_params = True
# Hide LiteLLM's extra console
litellm.suppress_debug_info = True


def convert_error(exc: Exception, provider_name: str, api_key: str = "") -> errors.GatewayError:
    

    
    message = str(exc)
    if api_key:
        message = message.replace(api_key, "***")
    message = " ".join(message.split())[:300]

    # Specific errors first, general errors last
    if isinstance(exc, litellm.ContentPolicyViolationError):
        return errors.ContentFilterError(message, provider=provider_name)

    if isinstance(exc, litellm.AuthenticationError):
        return errors.ProviderAuthError(message, provider=provider_name)

    if isinstance(exc, litellm.NotFoundError):
        return errors.ProviderModelNotFoundError(message, provider=provider_name)

    if isinstance(exc, litellm.RateLimitError):
        return errors.RateLimitError(message, provider=provider_name)

    if isinstance(exc, litellm.Timeout):
        return errors.ProviderTimeoutError(message, provider=provider_name)

    if isinstance(exc, litellm.APIConnectionError):
        return errors.ProviderConnectionError(message, provider=provider_name)

    if isinstance(exc, litellm.BadRequestError):
        return errors.BadRequestError(message, provider=provider_name)

    # Status_code based errors
    status = getattr(exc, "status_code", None)
    if status in (401, 403):
        return errors.ProviderAuthError(message, provider=provider_name)
    if status == 404:
        return errors.ProviderModelNotFoundError(message, provider=provider_name)
    if status == 429:
        return errors.RateLimitError(message, provider=provider_name)
    if status is not None and status >= 500:
        return errors.ProviderServerError(message, provider=provider_name)

    # Unknown error: treat it as a provider problem
    return errors.ProviderError(message, provider=provider_name)


async def call_provider(provider: Provider, request: ChatRequest, max_tokens: int) -> CallResult:
    

    api_key = provider.api_key.get_secret_value()   
    messages = [message.model_dump() for message in request.messages]

    # Only send options the client actually set
    options = {"max_tokens": max_tokens}
    if request.temperature is not None:
        options["temperature"] = request.temperature

    start = time.perf_counter()
    try:
        response = await litellm.acompletion(
            model=provider.model,        
            messages=messages,
            api_key=api_key,
            timeout=provider.timeout_seconds,
            num_retries=0,              
            **options,
        )
    except Exception as exc:

        latency_ms = (time.perf_counter() - start) * 1000
        error = convert_error(exc, provider.name, api_key)
        logger.warning(
            f"provider_call_failed provider={provider.name} "
            f"error_type={error.error_type} latency_ms={latency_ms:.0f} detail={error.message}"
        )
        raise error from exc

    latency_ms = (time.perf_counter() - start) * 1000

    
    if not response.choices:
        raise errors.ProviderServerError("Provider returned no answer", provider=provider.name)

    choice = response.choices[0]
    usage = response.usage

    result = CallResult(
        provider=provider.name,
        model=provider.model,
        content=choice.message.content or "",
        finish_reason=choice.finish_reason,
        prompt_tokens=(usage.prompt_tokens or 0) if usage else 0,
        completion_tokens=(usage.completion_tokens or 0) if usage else 0,
        latency_ms=latency_ms,
    )

    logger.info(
        f"provider_call_ok provider={provider.name} latency_ms={latency_ms:.0f} "
        f"tokens={result.prompt_tokens}+{result.completion_tokens}"
    )
    return result