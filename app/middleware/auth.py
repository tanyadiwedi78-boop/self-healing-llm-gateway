from fastapi import Depends, Request
from pydantic import ValidationError

from app.core.auth import TenantContext, get_tenant
from app.core.exceptions import InvalidMetadataError, MissingMetadataError
from app.schemas.metadata import RequestMetadata

INVALID_MESSAGE = (
    "Invalid header. X-Feature: a-z, 0-9, - or _ (max 40 characters). "
    "X-Request-Class: interactive or deferrable. Idempotency-Key: max 64 characters."
)


def get_metadata(
    request: Request,
    tenant: TenantContext = Depends(get_tenant),
) -> RequestMetadata:
    feature = request.headers.get("X-Feature", "").strip()
    if not feature:
        raise MissingMetadataError("Header X-Feature is required.")

    request_class = request.headers.get("X-Request-Class", "interactive").strip().lower()
    idempotency_key = request.headers.get("Idempotency-Key") or None

    try:
        return RequestMetadata(
            tenant_id=tenant.tenant_id,   # from the key, never from a header
            feature=feature,
            request_id=getattr(request.state, "request_id", "-"),
            request_class=request_class,
            idempotency_key=idempotency_key,
        )
    except ValidationError:
        raise InvalidMetadataError(INVALID_MESSAGE) from None