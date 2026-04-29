from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Implementación pendiente
        return await call_next(request)
