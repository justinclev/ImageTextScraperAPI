import time
from collections import defaultdict, deque
from threading import Lock
from typing import DefaultDict, Deque, Tuple

from src.core.settings import settings


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> Tuple[bool, int]:
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            events = self._events[key]
            while events and events[0] < window_start:
                events.popleft()

            if len(events) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry_after

            events.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


ocr_rate_limiter = InMemoryRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def check_ocr_rate_limit(client_key: str) -> Tuple[bool, int]:
    return ocr_rate_limiter.allow(client_key)


def reset_rate_limiter() -> None:
    ocr_rate_limiter.reset()
