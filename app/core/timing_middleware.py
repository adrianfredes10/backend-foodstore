# middleware: mide y loguea el tiempo de cada request
import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.timing")

# requests por encima de este umbral se loguean como warning
SLOW_MS = 500.0


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        response.headers["Server-Timing"] = (
            f'total;dur={duration_ms:.2f};desc="Total request time"'
        )
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"

        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        # print para asegurar visibilidad en consola (para el video)
        print(
            f'[app.timing] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)'
            ,
            flush=True,
        )

        if duration_ms > SLOW_MS:
            logger.warning(
                "request lento: %s %s (%.2fms)",
                request.method,
                request.url.path,
                duration_ms,
            )

        return response
