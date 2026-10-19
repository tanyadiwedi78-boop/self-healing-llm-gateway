from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """One message in the conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """The body of POST /v1/chat/completions."""

    # Ignore extra fields (like top_p) that OpenAI clients may send,
    # instead of rejecting the whole request.
    model_config = ConfigDict(extra="ignore")

    # Optional: if the client leaves it empty, the gateway picks the model.
    model: str | None = None

    # At least one message is required.
    messages: list[Message] = Field(min_length=1)

    # Optional limits. Pydantic rejects bad values automatically.
    max_tokens: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=None, ge=0, le=2)

    # Streaming is added in a later phase, so for now it must stay False.
    stream: bool = False
