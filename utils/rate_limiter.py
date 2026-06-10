import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """Sliding-window rate limiter for FastAPI endpoints.

    Usage:
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        @router.post("/endpoint")
        async def endpoint(request: Request, _=Depends(limiter)):
            ...
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # seconds
        self._start_cleanup()

    # ---- public API (used as FastAPI dependency) ----

    def __call__(self, request: Request) -> None:
        key = self._resolve_key(request)
        now = time.monotonic()

        with self._lock:
            bucket = self._buckets[key]
            cutoff = now - self.window_seconds

            # Prune timestamps outside the current window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                oldest = bucket[0]
                retry_after = int(self.window_seconds - (now - oldest))
                raise HTTPException(
                    status_code=429,
                    detail={
                        "msg": (
                            f"Muitas requisições. "
                            f"Tente novamente em {retry_after} segundos."
                        ),
                        "retry_after_seconds": retry_after,
                    },
                )

            bucket.append(now)

    # ---- helpers ----

    @staticmethod
    def _resolve_key(request: Request) -> str:
        """Use client IP as the rate-limit key."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client is not None else "unknown"

    def _start_cleanup(self) -> None:
        """Background thread that evicts stale buckets periodically."""

        def _cleanup() -> None:
            while True:
                time.sleep(self._cleanup_interval)
                now = time.monotonic()
                cutoff = now - self.window_seconds
                with self._lock:
                    stale_keys = [
                        k for k, v in self._buckets.items()
                        if not v or v[-1] < cutoff
                    ]
                    for k in stale_keys:
                        del self._buckets[k]

        thread = threading.Thread(target=_cleanup, daemon=True)
        thread.start()
