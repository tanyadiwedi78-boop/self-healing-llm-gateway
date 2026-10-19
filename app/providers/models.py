from pydantic import BaseModel, SecretStr


class Provider(BaseModel):
    # Settings of one provider. They never change while the app runs.
    # Live state (breaker, health) is stored in Redis

    name: str              
    model: str              
    api_key: SecretStr     
    timeout_seconds: float  
    enabled: bool = True    


class CallResult(BaseModel):
    # What one successful provider call returns

    provider: str
    model: str
    content: str                       
    finish_reason: str | None = None   
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0        