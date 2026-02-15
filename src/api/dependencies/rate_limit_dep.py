from abc import ABC, abstractmethod
from typing import Any

from fastapi import HTTPException, Request, WebSocket

from src.api.dependencies.injectables import MongoDBDep
from src.core.rate_limiting import RateLimiter


class LimitRequest(ABC):
    def __init__(self, max_requests=10, window_minutes=1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes

    def get_client_identifier(self, conn: Request | WebSocket):
        forwarded_for = conn.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return conn.client.host if conn.client else "unknown"

    def rate_limit_dependency(
        self,
        endpoint: str,
        conn: Request | WebSocket,
        rate_limiter: RateLimiter,
    ):
        identifier = self.get_client_identifier(conn)
        allowed, error_message = rate_limiter.is_allowed(identifier, endpoint)

        if not allowed:
            raise HTTPException(status_code=429, detail=error_message)

        return True

    @abstractmethod
    def get_endpoint_identifier(self, *args, **kwargs) -> str: ...


class LimitWebSocket(LimitRequest):
    def __init__(self, max_requests=10, window_minutes=1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes

    def get_endpoint_identifier(self, websocket: WebSocket) -> str:
        return f"WS {websocket.url.path}"

    async def __call__(self, websocket: WebSocket, db: MongoDBDep) -> Any:
        rate_limiter = RateLimiter(db, self.max_requests, self.window_minutes)
        endpoint = self.get_endpoint_identifier(websocket)
        return self.rate_limit_dependency(endpoint, websocket, rate_limiter)


class LimitEndpoint(LimitRequest):
    def __init__(self, max_requests=10, window_minutes=1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes

    def get_endpoint_identifier(self, request: Request) -> str:
        return f"{request.method}:{request.url.path}"

    def __call__(self, request: Request, db: MongoDBDep):
        rate_limiter = RateLimiter(db, self.max_requests, self.window_minutes)
        endpoint = self.get_endpoint_identifier(request)
        return self.rate_limit_dependency(endpoint, request, rate_limiter)
