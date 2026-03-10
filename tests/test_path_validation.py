"""Tests for centralized path containment validator and enforcement points."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.domain.path_validator import validate_path_within
from src.exceptions import InputError, PathTraversalError


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


class TestReaderPathValidation:
    """Tests for path validation in read_md_files."""

    def test_read_md_files_validates_path(self, tmp_path: Path) -> None:
        """read_md_files with path outside vault_base_dir raises PathTraversalError."""
        from src.infrastructure.reader import read_md_files

        with pytest.raises(PathTraversalError):
            read_md_files(["/etc/passwd"], vault_base_dir=str(tmp_path))

    def test_read_md_files_allows_valid_path(self, tmp_path: Path) -> None:
        """read_md_files with valid path under vault_base_dir succeeds."""
        from src.infrastructure.reader import read_md_files

        md_file = tmp_path / "notes" / "test.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# Test\nHello world")
        result = read_md_files([str(md_file)], vault_base_dir=str(tmp_path))
        assert "Hello world" in result

    def test_read_md_files_without_base_dir_skips_validation(self, tmp_path: Path) -> None:
        """read_md_files without vault_base_dir does not validate paths."""
        from src.infrastructure.reader import read_md_files

        md_file = tmp_path / "test.md"
        md_file.write_text("# Content")
        # No vault_base_dir passed -- should not raise even if path is "outside"
        result = read_md_files([str(md_file)])
        assert "Content" in result


class TestWriterPathValidation:
    """Tests for path validation in write_episode_to_vault."""

    def test_write_episode_validates_vault_output_dir(self, tmp_path: Path, sample_episode) -> None:
        """write_episode_to_vault with vault_output_dir outside vault_base_dir raises PathTraversalError."""
        from src.infrastructure.obsidian_writer import write_episode_to_vault

        mp3_file = tmp_path / "source.mp3"
        mp3_file.write_bytes(b"\x00" * 100)

        with pytest.raises(PathTraversalError):
            write_episode_to_vault(
                sample_episode,
                str(mp3_file),
                "transcript text",
                "/completely/outside/vault",
                vault_base_dir=str(tmp_path),
            )

    def test_write_episode_allows_valid_vault_output_dir(self, tmp_path: Path, sample_episode) -> None:
        """write_episode_to_vault with valid vault_output_dir succeeds."""
        from src.infrastructure.obsidian_writer import write_episode_to_vault

        mp3_file = tmp_path / "source.mp3"
        mp3_file.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "vault_output"
        output_dir.mkdir()

        mp3_dest, note_dest = write_episode_to_vault(
            sample_episode,
            str(mp3_file),
            "transcript text",
            str(output_dir),
            vault_base_dir=str(tmp_path),
        )
        assert os.path.exists(mp3_dest)
        assert os.path.exists(note_dest)


class TestWatcherPathValidation:
    """Tests for path validation in WatcherService.start()."""

    def test_watcher_skips_invalid_preset_path(self, tmp_path: Path, caplog) -> None:
        """Watcher start() skips presets with folder_path outside vault_base_dir."""
        from src.backend.watcher.service import WatcherService
        from src.domain.models import Preset

        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        settings = MagicMock()
        settings.vault_base_dir = str(vault_dir)

        invalid_preset = MagicMock(spec=Preset)
        invalid_preset.id = 1
        invalid_preset.folder_path = "/definitely/outside/vault"

        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)

        with patch(
            "src.backend.watcher.service.PresetRepository"
        ) as mock_repo_cls:
            mock_repo_cls.return_value.get_all.return_value = [invalid_preset]
            service = WatcherService(settings, mock_session_factory)

            with caplog.at_level(logging.WARNING):
                service.start()

        assert "outside vault" in caplog.text
        # Observer should not have been started (no valid folders)
        assert service._observer is None or not service.is_running

    def test_watcher_schedules_valid_preset_path(self, tmp_path: Path) -> None:
        """Watcher start() schedules presets with valid folder_path."""
        from src.backend.watcher.service import WatcherService
        from src.domain.models import Preset

        valid_folder = tmp_path / "vault" / "notes"
        valid_folder.mkdir(parents=True)
        settings = MagicMock()
        settings.vault_base_dir = str(tmp_path / "vault")
        settings.watcher_debounce_seconds = 1.5

        valid_preset = MagicMock(spec=Preset)
        valid_preset.id = 1
        valid_preset.folder_path = str(valid_folder)

        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)

        with patch(
            "src.backend.watcher.service.PresetRepository"
        ) as mock_repo_cls:
            mock_repo_cls.return_value.get_all.return_value = [valid_preset]
            service = WatcherService(settings, mock_session_factory)
            service.start()

        assert service.is_running
        service.stop()


class TestStartupPresetWarning:
    """Tests for startup warning on invalid preset paths."""

    def test_startup_logs_warning_for_invalid_presets(self, tmp_path: Path, caplog) -> None:
        """Watcher logs WARNING for existing presets with out-of-bounds paths."""
        from src.backend.watcher.service import WatcherService
        from src.domain.models import Preset

        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        settings = MagicMock()
        settings.vault_base_dir = str(vault_dir)

        bad_preset = MagicMock(spec=Preset)
        bad_preset.id = 42
        bad_preset.folder_path = "/etc/shadow"

        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)

        with patch(
            "src.backend.watcher.service.PresetRepository"
        ) as mock_repo_cls:
            mock_repo_cls.return_value.get_all.return_value = [bad_preset]
            service = WatcherService(settings, mock_session_factory)

            with caplog.at_level(logging.WARNING):
                service.start()

        # Should log a warning mentioning the preset and path issue
        assert any("outside vault" in r.message for r in caplog.records)


class TestPresetsPagePathBadge:
    """Tests for path_valid badge rendering on full-page presets load."""

    def test_presets_page_shows_valid_path(
        self, dashboard_client, session_factory, dashboard_settings
    ):
        """Full-page GET /dashboard/presets does NOT show 'Invalid path' for valid preset."""
        from src.infrastructure.database.models import HostRecord, PresetRecord, StyleRecord

        with session_factory() as session:
            host_a = HostRecord(name="HostA", voice="Kore", role="host")
            host_b = HostRecord(name="HostB", voice="Puck", role="co-host")
            style = StyleRecord(name="TestStyle", tone="informative")
            session.add_all([host_a, host_b, style])
            session.flush()
            # Use a valid path within vault_base_dir
            valid_folder = Path(dashboard_settings.vault_base_dir) / "notes"
            valid_folder.mkdir(exist_ok=True)
            preset = PresetRecord(
                folder_path=str(valid_folder),
                host_a_id=host_a.id,
                host_b_id=host_b.id,
                style_id=style.id,
            )
            session.add(preset)
            session.commit()

        resp = dashboard_client.get("/dashboard/presets")
        assert resp.status_code == 200
        assert "Invalid path" not in resp.text

    def test_presets_page_shows_invalid_badge(
        self, dashboard_client, session_factory, dashboard_settings
    ):
        """Full-page GET /dashboard/presets shows 'Invalid path' badge for out-of-bounds preset."""
        from src.infrastructure.database.models import HostRecord, PresetRecord, StyleRecord

        with session_factory() as session:
            host_a = HostRecord(name="HostA2", voice="Kore", role="host")
            host_b = HostRecord(name="HostB2", voice="Puck", role="co-host")
            style = StyleRecord(name="TestStyle2", tone="informative")
            session.add_all([host_a, host_b, style])
            session.flush()
            preset = PresetRecord(
                folder_path="../../../etc",
                host_a_id=host_a.id,
                host_b_id=host_b.id,
                style_id=style.id,
            )
            session.add(preset)
            session.commit()

        resp = dashboard_client.get("/dashboard/presets")
        assert resp.status_code == 200
        assert "Invalid path" in resp.text
