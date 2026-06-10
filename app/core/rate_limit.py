# rate limit por IP en endpoints sensibles (login/register)
# algoritmo token bucket en memoria (single-process, suficiente para el TPI)
import threading
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens por segundo
        self.tokens = capacity
        self.last = time.monotonic()
        self._lock = threading.Lock()

    def try_consume(self) -> bool:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(
                self.capacity, self.tokens + (now - self.last) * self.refill_rate
            )
            self.last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    # solo se limita login y register (resto pasa libre)
    AUTH_PATHS = ("/api/v1/auth/login", "/api/v1/auth/register")

    def __init__(self, app):
        super().__init__(app)
        s = get_settings()
        self.capacity = float(s.RATE_LIMIT_AUTH_MAX)
        # max intentos por ventana -> tokens por segundo
        self.refill_rate = s.RATE_LIMIT_AUTH_MAX / (
            s.RATE_LIMIT_AUTH_WINDOW_MINUTES * 60.0
        )
        self.retry_after = int(1 / self.refill_rate)
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _bucket(self, key: str) -> TokenBucket:
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(self.capacity, self.refill_rate)
            return self._buckets[key]

    @staticmethod
    def _client_ip(request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self.AUTH_PATHS:
            return await call_next(request)

        key = self._client_ip(request)
        if not self._bucket(key).try_consume():
            body = (
                '{"type":"https://foodstore.local/errors/rate-limit-exceeded",'
                '"title":"Too Many Requests","status":429,'
                '"detail":"Demasiados intentos. Intenta de nuevo mas tarde.",'
                f'"instance":"{request.url.path}"}}'
            )
            return Response(
                content=body,
                status_code=429,
                media_type="application/problem+json",
                headers={"Retry-After": str(self.retry_after)},
            )
        return await call_next(request)
