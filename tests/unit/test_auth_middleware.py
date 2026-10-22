from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.auth import TenantContext, get_tenant
from app.core.exceptions import GatewayError
from app.middleware.auth import get_metadata
from app.middleware.request_id import RequestIdMiddleware
from app.schemas.metadata import RequestMetadata


def make_client(logged_in=True):
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(GatewayError)
    async def handle_error(request, error):
        return JSONResponse(status_code=error.http_status, content=error.to_dict())

    @app.get("/meta")
    async def meta(metadata: RequestMetadata = Depends(get_metadata)):
        return metadata.model_dump()

    if logged_in:
        app.dependency_overrides[get_tenant] = lambda: TenantContext(tenant_id="tenant-a")
    return TestClient(app)


def test_valid_request_builds_metadata():
    response = make_client().get("/meta", headers={"X-Feature": "chat-summary"})
    data = response.json()
    assert response.status_code == 200
    assert data["tenant_id"] == "tenant-a"
    assert data["feature"] == "chat-summary"
    assert data["request_class"] == "interactive"
    assert data["request_id"] == response.headers["X-Request-Id"]


def test_tenant_comes_from_the_key_not_a_header():
    headers = {"X-Feature": "x", "X-Tenant": "someone-else", "X-Tenant-Id": "someone-else"}
    assert make_client().get("/meta", headers=headers).json()["tenant_id"] == "tenant-a"


def test_missing_feature_is_rejected():
    response = make_client().get("/meta")
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "missing_metadata"


def test_bad_feature_is_rejected():
    response = make_client().get("/meta", headers={"X-Feature": "Bad Feature!"})
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_metadata"


def test_bad_request_class_is_rejected():
    headers = {"X-Feature": "x", "X-Request-Class": "urgent"}
    assert make_client().get("/meta", headers=headers).status_code == 400


def test_deferrable_class_and_idempotency_key_are_accepted():
    headers = {"X-Feature": "x", "X-Request-Class": "Deferrable", "Idempotency-Key": "job-1"}
    data = make_client().get("/meta", headers=headers).json()
    assert data["request_class"] == "deferrable"
    assert data["idempotency_key"] == "job-1"


def test_no_api_key_gives_401():
    response = make_client(logged_in=False).get("/meta", headers={"X-Feature": "x"})
    assert response.status_code == 401