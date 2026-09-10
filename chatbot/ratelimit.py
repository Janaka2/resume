# ratelimit.py — small in-memory per-client token bucket.
import threading
import time


class TokenBucket:
    """Allow `capacity` requests per `period` seconds, per key, refilled continuously."""

    def __init__(self, capacity: int = 20, period: float = 600.0):
        self.capacity = capacity
        self.rate = capacity / period  # tokens per second
        self._buckets = {}  # key -> [tokens, last_refill_ts]
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(float(self.capacity), tokens + (now - last) * self.rate)
            if tokens < 1.0:
                self._buckets[key] = [tokens, now]
                return False
            self._buckets[key] = [tokens - 1.0, now]
            # keep the dict from growing forever: drop buckets idle for a full period
            if len(self._buckets) > 5000:
                stale = now - self.capacity / self.rate
                for k in [k for k, (_, ts) in self._buckets.items() if ts < stale]:
                    self._buckets.pop(k, None)
            return True


def client_key(request) -> str:
    """Best-effort client identifier from a gr.Request; falls back to a shared key.

    Behind the Hugging Face proxy request.client.host is the proxy itself, so the
    first X-Forwarded-For entry is preferred when present.
    """
    try:
        host = ""
        if request is not None:
            host = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            if not host and request.client:
                host = request.client.host or ""
        return host or "unknown"
    except Exception:
        return "unknown"
