import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        # generate unique ID for this request
        request_id = str(uuid.uuid4())[:8]

        # bind request context to all logs within this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()

        logger.info("request started")

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("request failed", exc_info=exc)
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # attach request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response