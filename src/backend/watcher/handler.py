"""Debounced watchdog handler that fires callbacks only for new .md files."""

from __future__ import annotations

import threading
from collections.abc import Callable

from watchdog.events import FileSystemEventHandler, FileSystemEvent


class DebouncedMarkdownHandler(FileSystemEventHandler):
    """Watches for .md file creation events with timer-based debounce.

    Rapid duplicate events for the same path reset the timer so only a
    single callback fires after the debounce period elapses.
    """

    def __init__(
        self,
        on_file_ready: Callable[[str], None],
        debounce_seconds: float = 1.5,
    ) -> None:
        super().__init__()
        self._on_file_ready = on_file_ready
        self._debounce_seconds = debounce_seconds
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Watchdog override
    # ------------------------------------------------------------------

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path: str = event.src_path
        if not path.endswith(".md"):
            return

        with self._lock:
            existing = self._timers.get(path)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(self._debounce_seconds, self._fire, args=(path,))
            timer.daemon = True
            timer.start()
            self._timers[path] = timer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fire(self, path: str) -> None:
        with self._lock:
            self._timers.pop(path, None)
        self._on_file_ready(path)

    def cleanup(self) -> None:
        """Cancel all pending timers. Call during shutdown."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
