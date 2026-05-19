import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = deque()

    def allow_request(self) -> bool:
        now = time.monotonic()
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def reset(self):
        self.requests.clear()