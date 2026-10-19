from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """One message in the conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """The body of POST /v1/chat/completions."""

    

    model_config = ConfigDict(extra="ignore")

    model: str | None = No

    messages: list[Message] = Field(min_length=1)

    # Optional limits. Pydantic rejects bad values automatically.
    max_tokens: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=None, ge=0, le=2)

    
    stream: bool = False
