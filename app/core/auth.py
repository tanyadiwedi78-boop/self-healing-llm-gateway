import hashlib
import json
import secrets
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError


class TenantContext(BaseModel):
    """Who is calling the gateway."""
    tenant_id: str
    tier: str = "standard"    # pricing level: "standard" or "enterprise"
    role: str = "tenant"      # permission level: "tenant" or "admin"


def hash_key(api_key: str) -> str:
    """Turn an API key into a SHA-256 hash.
    We store only hashes in tenants.json, so a leaked file does not leak real keys."""
    return hashlib.sha256(api_key.encode()).hexdigest()


@lru_cache
def load_tenants() -> dict:
    """Read tenants.json once and remember the result.
    The file looks like: { "<hash of key>": {"tenant_id": "...", "tier": "..."} }"""
    path = Path(get_settings().tenants_file)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_api_key(request: Request) -> str | None:
    """Find the key in 'Authorization: Bearer <key>' or in 'X-API-Key: <key>'."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()

    x_api_key = request.headers.get("X-API-Key", "")
    return x_api_key.strip() or None


def is_master_key(api_key: str) -> bool:
    """Check the key against GATEWAY_API_KEY from .env.
    compare_digest is a safe way to compare secrets (it avoids timing attacks)."""
    master_key = get_settings().gateway_api_key.get_secret_value()
    if not master_key:       
        return False
    return secrets.compare_digest(api_key, master_key)


# ---------- FastAPI dependencies (used inside routers) ----------

def get_tenant(request: Request) -> TenantContext:
    """Return the caller's identity, or raise 401 if the key is missing or wrong."""
    api_key = get_api_key(request)
    if api_key is None:
        raise UnauthorizedError("Missing API key.")

    if is_master_key(api_key):
        tenant = TenantContext(tenant_id="admin", tier="enterprise", role="admin")
    else:
        info = load_tenants().get(hash_key(api_key))
        if info is None:
            raise UnauthorizedError("Invalid API key.")
        tenant = TenantContext(tenant_id=info["tenant_id"], tier=info.get("tier", "standard"))

    request.state.tenant = tenant     # other layers (logging, metrics) can read it
    return tenant


def require_admin(tenant: TenantContext = Depends(get_tenant)) -> TenantContext:
    """Use this on admin and chaos routes. Normal tenants get a 403."""
    if tenant.role != "admin":
        raise ForbiddenError("Admin access required.")
    return tenant