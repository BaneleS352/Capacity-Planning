from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import correlation_id_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))[:128]
        request.state.correlation_id = correlation_id
        token = correlation_id_context.set(correlation_id)
        started = perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time-Ms"] = f"{(perf_counter() - started) * 1000:.2f}"
            return response
        finally:
            correlation_id_context.reset(token)
