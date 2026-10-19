from typing import Literal

from pydantic import BaseModel, Field


class RequestMetadata(BaseModel):
    """Require metadata on every request: tenant, feature, and request id."""

    
    tenant_id: str


    feature: str = Field(pattern=r"^[a-z0-9_-]{1,40}$")

    # Unique id of this request. Used in logs, metrics, and the queue.
    request_id: str = Field(min_length=1, max_length=64)

    # "interactive": a user is waiting, so fail fast.
    # "deferrable": can wait, so it may be queued and retried later (Phase 4).
    request_class: Literal["interactive", "deferrable"] = "interactive"

    # Optional. Phase 4 needs it so a retried request cannot run its side effect twice.
    idempotency_key: str | None = Field(default=None, max_length=64)
