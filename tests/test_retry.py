"""Tests for retry_with_backoff — exponential backoff with 429 awareness."""

import threading
from unittest.mock import MagicMock, call

import pytest

from src.application.retry import retry_with_backoff
from src.exceptions import RateLimitError, ScriptGenerationError, TTSError

DEFAULTS = dict(
    max_retries=3,
    backoff_initial=1.0,
    backoff_multiplier=2.0,
    backoff_max=300.0,
)


def _make_shutdown() -> MagicMock:
    """Return a mock shutdown_event whose .wait() returns False (no shutdown)."""
    ev = MagicMock(spec=threading.Event)
    ev.wait.return_value = False
    return ev


class TestSuccessPath:
    def test_returns_immediately_on_success(self):
        fn = MagicMock(return_value="ok")
        result = retry_with_backoff(fn, shutdown_event=_make_shutdown(), **DEFAULTS)
        assert result == "ok"
        fn.assert_called_once()


class TestTransientRetries:
    def test_retries_and_succeeds(self):
        fn = MagicMock(side_effect=[ScriptGenerationError("fail"), "ok"])
        result = retry_with_backoff(fn, shutdown_event=_make_shutdown(), **DEFAULTS)
        assert result == "ok"
        assert fn.call_count == 2

    def test_max_retries_exhausted_reraises(self):
        fn = MagicMock(side_effect=ScriptGenerationError("fail"))
        with pytest.raises(ScriptGenerationError, match="fail"):
            retry_with_backoff(fn, shutdown_event=_make_shutdown(), **DEFAULTS)
        assert fn.call_count == 4  # 1 initial + 3 retries

    def test_tts_error_also_retries(self):
        fn = MagicMock(side_effect=[TTSError("tts fail"), "ok"])
        result = retry_with_backoff(fn, shutdown_event=_make_shutdown(), **DEFAULTS)
        assert result == "ok"
        assert fn.call_count == 2


class TestRateLimitHandling:
    def test_429_does_not_count_against_retries(self):
        # 5 rate limits then success -- should work with max_retries=3
        fn = MagicMock(
            side_effect=[RateLimitError("429")] * 5 + ["ok"],
        )
        result = retry_with_backoff(fn, shutdown_event=_make_shutdown(), **DEFAULTS)
        assert result == "ok"
        assert fn.call_count == 6

    def test_retry_after_passed_to_wait(self):
        fn = MagicMock(
            side_effect=[RateLimitError("429", retry_after=10.0), "ok"],
        )
        ev = _make_shutdown()
        retry_with_backoff(fn, shutdown_event=ev, **DEFAULTS)
        ev.wait.assert_called_once_with(10.0)


class TestBackoffCalculation:
    def test_exponential_backoff_values(self):
        fn = MagicMock(
            side_effect=[
                ScriptGenerationError("e"),
                ScriptGenerationError("e"),
                ScriptGenerationError("e"),
                "ok",
            ],
        )
        ev = _make_shutdown()
        retry_with_backoff(fn, shutdown_event=ev, backoff_initial=1.0, backoff_multiplier=2.0,
                           backoff_max=300.0, max_retries=3)
        # waits: 1*2^0=1, 1*2^1=2, 1*2^2=4
        assert ev.wait.call_args_list == [call(1.0), call(2.0), call(4.0)]

    def test_backoff_capped_at_max(self):
        fn = MagicMock(
            side_effect=[
                ScriptGenerationError("e"),
                ScriptGenerationError("e"),
                ScriptGenerationError("e"),
                "ok",
            ],
        )
        ev = _make_shutdown()
        retry_with_backoff(fn, shutdown_event=ev, backoff_initial=1.0, backoff_multiplier=2.0,
                           backoff_max=3.0, max_retries=3)
        # waits: 1, 2, min(4,3)=3
        assert ev.wait.call_args_list == [call(1.0), call(2.0), call(3.0)]


class TestShutdown:
    def test_shutdown_during_wait_raises(self):
        fn = MagicMock(side_effect=ScriptGenerationError("fail"))
        ev = MagicMock(spec=threading.Event)
        ev.wait.return_value = True  # shutdown signaled
        with pytest.raises(InterruptedError, match="Shutdown"):
            retry_with_backoff(fn, shutdown_event=ev, **DEFAULTS)
