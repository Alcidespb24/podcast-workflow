"""Tests for DebouncedMarkdownHandler — .md filtering and debounce logic."""

import time
from unittest.mock import MagicMock

import pytest
from watchdog.events import FileCreatedEvent, DirCreatedEvent

from src.backend.watcher.handler import DebouncedMarkdownHandler

DEBOUNCE = 0.1  # short debounce for fast tests


@pytest.fixture()
def callback():
    return MagicMock()


@pytest.fixture()
def handler(callback):
    h = DebouncedMarkdownHandler(on_file_ready=callback, debounce_seconds=DEBOUNCE)
    yield h
    h.cleanup()


class TestMarkdownFiltering:
    """Handler must only react to .md file-creation events."""

    def test_directory_event_ignored(self, handler, callback):
        event = DirCreatedEvent(src_path="/notes/new_dir")
        handler.on_created(event)
        time.sleep(DEBOUNCE + 0.1)
        callback.assert_not_called()

    def test_non_md_file_ignored(self, handler, callback):
        event = FileCreatedEvent(src_path="/notes/readme.txt")
        handler.on_created(event)
        time.sleep(DEBOUNCE + 0.1)
        callback.assert_not_called()

    def test_md_file_fires_callback(self, handler, callback):
        event = FileCreatedEvent(src_path="/notes/topic.md")
        handler.on_created(event)
        time.sleep(DEBOUNCE + 0.15)
        callback.assert_called_once_with("/notes/topic.md")


class TestDebounce:
    """Rapid duplicate events for the same path must consolidate."""

    def test_rapid_duplicates_single_callback(self, handler, callback):
        event = FileCreatedEvent(src_path="/notes/topic.md")
        for _ in range(3):
            handler.on_created(event)
            time.sleep(0.02)
        time.sleep(DEBOUNCE + 0.15)
        callback.assert_called_once_with("/notes/topic.md")

    def test_different_paths_independent(self, handler, callback):
        e1 = FileCreatedEvent(src_path="/notes/a.md")
        e2 = FileCreatedEvent(src_path="/notes/b.md")
        handler.on_created(e1)
        handler.on_created(e2)
        time.sleep(DEBOUNCE + 0.15)
        assert callback.call_count == 2

    def test_cleanup_cancels_pending(self, handler, callback):
        event = FileCreatedEvent(src_path="/notes/topic.md")
        handler.on_created(event)
        handler.cleanup()
        time.sleep(DEBOUNCE + 0.15)
        callback.assert_not_called()
