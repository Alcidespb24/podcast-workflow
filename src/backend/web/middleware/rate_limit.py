"""Login rate limiter to protect against brute-force attacks."""

import threading
import time


class LoginRateLimiter:
    """In-memory rate limiter for login attempts, keyed by client IP.

    Tracks failed login timestamps per IP and blocks further attempts
    after max_attempts within window_seconds.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, ip: str) -> tuple[bool, int]:
        """Check if a login attempt is allowed for the given IP.

        Returns:
            (allowed, retry_after_minutes) -- allowed is True if under limit,
            retry_after_minutes is the wait time when blocked (0 if allowed).
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            attempts = self._attempts.get(ip, [])
            # Prune expired attempts
            attempts = [t for t in attempts if t > cutoff]
            self._attempts[ip] = attempts

            if len(attempts) >= self.max_attempts:
                oldest = attempts[0]
                retry_after = int((oldest + self.window_seconds - now) / 60) + 1
                return False, retry_after

        return True, 0

    def record(self, ip: str) -> None:
        """Record a failed login attempt for the given IP."""
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                self._attempts[ip] = []
            self._attempts[ip].append(now)
