class GatewayError(Exception):
    http_status: int = 500
    error_type: str = "gateway_error"
    retryable: bool = False
    counts_against_provider: bool = False

    def __init__(self, message: str = "", *, provider: str | None = None):
        super().__init__(message)
        self.message = message
        self.provider = provider

    def to_dict(self) -> dict:
        """OpenAI-style error body so existing clients can parse it."""
        return {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "provider": self.provider,
            }
        }


# ---------- Errors coming from a provider ----------

class ProviderError(GatewayError):
    """Base class: a provider call failed."""
    http_status = 502
    error_type = "provider_error"
    retryable = True
    counts_against_provider = True


class RateLimitError(ProviderError):
    http_status = 429
    error_type = "rate_limit"


class ProviderTimeoutError(ProviderError):
    http_status = 504
    error_type = "timeout"


class ProviderServerError(ProviderError):
    """Provider returned a 5xx response."""
    error_type = "server_error"


class ProviderConnectionError(ProviderError):
    """Network-level failure: the provider could not be reached."""
    error_type = "connection_error"


class ProviderAuthError(ProviderError):
    """The provider API key is invalid or expired. This is our configuration
    problem, so retrying is pointless, but the provider must be marked unhealthy."""
    error_type = "provider_auth"
    retryable = False


class ContentFilterError(ProviderError):
    """The provider blocked the content. The provider itself is healthy,
    so this does not count against its health."""
    http_status = 400
    error_type = "content_filter"
    retryable = False
    counts_against_provider = False


class BadRequestError(ProviderError):
    """The request itself was invalid (the caller's mistake), not the provider's."""
    http_status = 400
    error_type = "bad_request"
    retryable = False
    counts_against_provider = False


# ---------- Gateway-level errors ----------

class CircuitOpenError(GatewayError):
    """The breaker is open, so the provider was not called at all.
    It does not count against health because no call was made."""
    http_status = 503
    error_type = "circuit_open"
    retryable = True


class AllProvidersFailedError(GatewayError):
    """Every provider in the fallback chain failed."""
    http_status = 503
    error_type = "all_providers_failed"

    def __init__(self, message: str = "", *, attempts: list[str] | None = None):
        super().__init__(message)
        self.attempts = attempts or []   # e.g. ["groq:rate_limit", "openai:timeout"]


class MissingMetadataError(GatewayError):
    """Tenant, feature, or request id is missing."""
    http_status = 400
    error_type = "missing_metadata"


class UnauthorizedError(GatewayError):
    """The client's gateway API key is invalid."""
    http_status = 401
    error_type = "unauthorized"

class ForbiddenError(GatewayError):
    """Logged in, but not allowed to do this."""
    http_status = 403
    error_type = "forbidden"


class ProviderModelNotFoundError(ProviderError):
    # Model name is wrong or retired (HTTP 404)
    error_type = "model_not_found"
    retryable = False