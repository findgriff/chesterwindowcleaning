"""In-memory token-bucket rate limiter, per IP.

Doesn't survive process restart. Acceptable for solo-trader scale.
Two instances run side-by-side in app.py: one for /api/chat,
one for /api/lead.
"""
from __future__ import annotations
import threading
import time


class RateLimiter:
    def __init__(self, *, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._buckets: dict[str, tuple[float, float]] = {}  # ip -> (tokens, last_seen)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)
            if tokens < 1.0:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1.0, now)
            return True
