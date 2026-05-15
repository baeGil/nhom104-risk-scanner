"""API middleware — error handling, logging, request timing."""
from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next) -> Response:
    """
    Global error handler middleware.

    Catches all exceptions and returns user-friendly error responses.
    """
    start_time = time.time()

    try:
        response = await call_next(request)

        # Log request timing
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")

        return response

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{request.method} {request.url.path} - ERROR - {duration:.3f}s - {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": str(e) if str(e) else "An unexpected error occurred",
            },
        )
