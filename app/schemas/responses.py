from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    role: str = "assistant"
    content: str | None = None


class ChoiceResponse(BaseModel):
    index: int = 0
    message: ChatMessageResponse
    finish_reason: str | None = None    # copied from the provider


class UsageResponse(BaseModel):
    # Token counts from the provider
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GatewayMetadata(BaseModel):
    # Extra info added by our gateway
    provider: str                  
    request_id: str
    latency_ms: float              # time spent in the gateway
    cost_usd: float = 0.0          # from our own pricing.json
    fallback_used: bool = False    # True if another provider had to answer
    attempts: list[str] = Field(default_factory=list)   # failed tries, e.g. ["groq:rate_limit"]
    cached: bool = False          


class ChatCompletionResponse(BaseModel):
    # OpenAI-style response plus our gateway info
    id: str
    object: str = "chat.completion"
    created: int                   # unix time in seconds
    model: str                     # model that really answered
    choices: list[ChoiceResponse]
    usage: UsageResponse
    gateway_metadata: GatewayMetadata