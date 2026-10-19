from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    role: str = "assistant"
    content: str | None = None


class ChoiceResponse(BaseModel):
    index: int = 0
    message: ChatMessageResponse
    finish_reason: str | None = None


class UsageResponse(BaseModel):
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GatewayMetadata(BaseModel):
    # Extra info added by our gateway
    provider: str                  
    request_id: str
    latency_ms: float              
    cost_usd: float = 0.0          
    fallback_used: bool = False    
    attempts: list[str] = Field(default_factory=list)   # failed tries, e.g. ["groq:rate_limit"]
    cached: bool = False          


class ChatCompletionResponse(BaseModel):
    # OpenAI-style response 
    id: str
    object: str = "chat.completion"
    created: int                   
    model: str                     
    choices: list[ChoiceResponse]
    usage: UsageResponse
    gateway_metadata: GatewayMetadata