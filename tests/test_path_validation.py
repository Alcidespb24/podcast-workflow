"""Tests for centralized path containment validator."""

import os
import sys
from pathlib import Path

import pytest

from src.domain.path_validator import validate_path_within
from src.exceptions import PathTraversalError


class TestValidatePathWithin:
    """Unit tests for validate_path_within()."""

    def test_valid_path_under_base_dir(self, tmp_path: Path) -> None:
        """Returns resolved Path when path is within base_dir."""
        subdir = tmp_path / "notes" / "podcasts"
        subdir.mkdir(parents=True)
        result = validate_path_within("notes/podcasts", tmp_path)
        assert result == subdir.resolve()

    def test_traversal_attempt_raises(self, tmp_path: Path) -> None:
        """Rejects ../traversal that escapes base_dir."""
        with pytest.raises(PathTraversalError):
            validate_path_within("notes/../../../etc/passwd", tmp_path)

    def test_absolute_escape_raises(self, tmp_path: Path) -> None:
        """Rejects absolute paths outside base_dir."""
        with pytest.raises(PathTraversalError):
            validate_path_within("/etc/passwd", tmp_path)

    def test_safe_relative_navigation(self, tmp_path: Path) -> None:
        """Allows safe relative navigation that stays inside base_dir."""
        (tmp_path / "notes" / "podcasts").mkdir(parents=True)
        result = validate_path_within("notes/safe/../podcasts", tmp_path)
        assert result == (tmp_path / "notes" / "podcasts").resolve()

    @pytest.mark.skipif(
        sys.platform == "win32" and not os.getenv("CI"),
        reason="os.symlink requires elevated privileges on Windows outside CI",
    )
    def test_symlink_escape_raises(self, tmp_path: Path) -> None:
        """Rejects symlinks that resolve outside base_dir."""
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("sensitive")

        inside = tmp_path / "vault"
        inside.mkdir()
        link = inside / "escape"
        link.symlink_to(outside)

        with pytest.raises(PathTraversalError):
            validate_path_within("escape/secret.txt", inside)

    def test_nonexistent_path_under_base_succeeds(self, tmp_path: Path) -> None:
        """Non-existent path under base_dir succeeds (strict=False)."""
        result = validate_path_within("notes/new/file.md", tmp_path)
        assert result == (tmp_path / "notes" / "new" / "file.md").resolve()

    def test_error_message_is_generic(self, tmp_path: Path) -> None:
        """PathTraversalError message does not reveal directory structure."""
        with pytest.raises(PathTraversalError, match="Path escapes allowed directory"):
            validate_path_within("../../etc/passwd", tmp_path)

    def test_accepts_str_arguments(self, tmp_path: Path) -> None:
        """Accepts str for both path and base_dir."""
        result = validate_path_within("notes", str(tmp_path))
        assert isinstance(result, Path)

    def test_accepts_path_arguments(self, tmp_path: Path) -> None:
        """Accepts Path objects for both path and base_dir."""
        result = validate_path_within(Path("notes"), tmp_path)
        assert isinstance(result, Path)
