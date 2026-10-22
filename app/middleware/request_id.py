import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_var

HEADER_NAME = "X-Request-Id"

# A client id is accepted only if it is short and uses safe characters
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def make_request_id(incoming: str | None) -> str:
    # Reuse if safe , otherwise make another one
    if incoming and SAFE_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


class RequestIdMiddleware(BaseHTTPMiddleware):
    

    async def dispatch(self, request, call_next):
        request_id = make_request_id(request.headers.get(HEADER_NAME))

        request.state.request_id = request_id       
        token = request_id_var.set(request_id)    
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)           

        response.headers[HEADER_NAME] = request_id  
        return response