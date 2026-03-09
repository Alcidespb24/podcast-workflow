"""Retry with exponential backoff and 429 rate-limit awareness."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TypeVar

from src.exceptions import RateLimitError, ScriptGenerationError, TTSError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int,
    backoff_initial: float,
    backoff_multiplier: float,
    backoff_max: float,
    shutdown_event: threading.Event,
) -> T:
    """Call *fn* with retries on transient errors and 429 rate-limit handling.

    * ``ScriptGenerationError`` / ``TTSError`` count against *max_retries*.
    * ``RateLimitError`` retries indefinitely (does **not** increment counter).
    * Backoff formula: ``initial * multiplier ** retries``, capped at *backoff_max*.
    * Rate-limit waits use the server's Retry-After value when available,
      otherwise a fixed delay (no exponential growth).
    * If *shutdown_event* is set during a wait, ``InterruptedError`` is raised.
    """
    retries = 0

    while True:
        try:
            return fn()
        except RateLimitError as exc:
            # Use server-provided delay, or a fixed fallback (no exponential growth)
            delay = exc.retry_after if exc.retry_after is not None else backoff_initial
            logger.warning("Rate-limited (429). Waiting %.1fs before retry.", delay)
            if shutdown_event.wait(delay):
                raise InterruptedError("Shutdown requested during backoff") from exc
        except (ScriptGenerationError, TTSError) as exc:
            retries += 1
            if retries > max_retries:
                raise
            delay = _backoff(retries - 1, backoff_initial, backoff_multiplier, backoff_max)
            logger.warning(
                "Transient error (attempt %d/%d): %s. Waiting %.1fs.",
                retries, max_retries, exc, delay,
            )
            if shutdown_event.wait(delay):
                raise InterruptedError("Shutdown requested during backoff") from exc


def _backoff(attempt: int, initial: float, multiplier: float, maximum: float) -> float:
    return min(initial * multiplier ** attempt, maximum)
