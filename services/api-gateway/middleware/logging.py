"""
Logging middleware
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""

    async def dispatch(self, request: Request, call_next):
        """Process request with logging"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started - {request.method} {request.url.path} "
            f"[{request_id}] from {self._get_client_ip(request)}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed - {request.method} {request.url.path} "
                f"[{request_id}] {response.status_code} in {duration:.3f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed - {request.method} {request.url.path} "
                f"[{request_id}] {str(e)} after {duration:.3f}s"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"
