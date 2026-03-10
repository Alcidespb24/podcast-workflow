"""Tests for application settings and startup validation."""

import sys
from pathlib import Path

import pytest
from argon2 import PasswordHasher
from pydantic import ValidationError

from src.config import Settings, load_settings

_ph = PasswordHasher()
TEST_HASH = _ph.hash("testpass")


class TestSettings:
    def test_settings_loads_from_env_file(self, tmp_env_file) -> None:
        settings = Settings(_env_file=tmp_env_file)
        assert settings.google_api_key == "test-key-123"
        assert settings.database_url == "sqlite:///test.db"

    def test_settings_default_database_url(self, tmp_path) -> None:
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            f"VAULT_BASE_DIR={vault_base}\n"
            f"VAULT_OUTPUT_DIR={vault_output}\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
            "SESSION_SECRET_KEY=test-secret\n"
        )
        settings = Settings(_env_file=env_file)
        assert settings.database_url == "sqlite:///data/podcast.db"

    def test_settings_default_hosts(self, tmp_path) -> None:
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            f"VAULT_BASE_DIR={vault_base}\n"
            f"VAULT_OUTPUT_DIR={vault_output}\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
            "SESSION_SECRET_KEY=test-secret\n"
        )
        settings = Settings(_env_file=env_file)
        assert isinstance(settings.default_host_a_name, str)
        assert isinstance(settings.default_host_a_voice, str)
        assert isinstance(settings.default_host_b_name, str)
        assert isinstance(settings.default_host_b_voice, str)


class TestStartupValidation:
    def test_missing_password_hash_raises(self, tmp_path) -> None:
        """Settings rejects instantiation when DASHBOARD_PASSWORD_HASH is missing."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            f"VAULT_BASE_DIR={vault_base}\n"
            f"VAULT_OUTPUT_DIR={vault_output}\n"
        )
        with pytest.raises(ValidationError):
            Settings(_env_file=env_file)

    def test_malformed_password_hash_raises(self, tmp_path) -> None:
        """Settings rejects a DASHBOARD_PASSWORD_HASH that is not Argon2id."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        with pytest.raises(ValidationError, match="Argon2id"):
            Settings(
                google_api_key="test-key",
                base_url="https://example.com",
                vault_base_dir=str(vault_base),
                vault_output_dir=str(vault_output),
                dashboard_password_hash="not-a-hash",
                session_secret_key="test-secret",
            )

    def test_valid_argon2id_hash_accepted(self, tmp_path) -> None:
        """Settings accepts a valid Argon2id hash string."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        settings = Settings(
            google_api_key="test-key",
            base_url="https://example.com",
            vault_base_dir=str(vault_base),
            vault_output_dir=str(vault_output),
            dashboard_password_hash=TEST_HASH,
            session_secret_key="test-secret",
        )
        assert settings.dashboard_password_hash == TEST_HASH

    def test_load_settings_prints_checklist_on_error(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """load_settings() prints a formatted error checklist and exits on invalid config."""
        env_file = tmp_path / ".env"
        env_file.write_text("")  # empty -- all required vars missing

        with pytest.raises(SystemExit) as exc_info:
            load_settings(_env_file=env_file)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Check that the error output contains UPPERCASE env var names
        assert "GOOGLE_API_KEY" in captured.out
        assert "DASHBOARD_PASSWORD_HASH" in captured.out
        assert "VAULT_BASE_DIR" in captured.out

    def test_load_settings_returns_settings_on_valid_config(self, tmp_path) -> None:
        """load_settings() returns a Settings instance when config is valid."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            f"VAULT_BASE_DIR={vault_base}\n"
            f"VAULT_OUTPUT_DIR={vault_output}\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
            "SESSION_SECRET_KEY=test-secret\n"
        )
        settings = load_settings(_env_file=env_file)
        assert isinstance(settings, Settings)
        assert settings.google_api_key == "test-key"


class TestVaultBaseDirValidation:
    """Tests for VAULT_BASE_DIR startup validation."""

    def test_missing_vault_base_dir_raises(self, tmp_path) -> None:
        """Settings without VAULT_BASE_DIR raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(
                google_api_key="test-key",
                base_url="https://example.com",
                vault_output_dir=str(tmp_path / "output"),
                dashboard_password_hash=TEST_HASH,
                session_secret_key="test-secret",
            )

    def test_vault_base_dir_nonexistent_raises(self, tmp_path) -> None:
        """Settings with non-existent VAULT_BASE_DIR directory raises ValidationError."""
        with pytest.raises(ValidationError, match="directory does not exist"):
            Settings(
                google_api_key="test-key",
                base_url="https://example.com",
                vault_base_dir=str(tmp_path / "nonexistent"),
                vault_output_dir=str(tmp_path / "nonexistent" / "output"),
                dashboard_password_hash=TEST_HASH,
                session_secret_key="test-secret",
            )

    def test_vault_base_dir_resolves_to_real_path(self, tmp_path) -> None:
        """Stored vault_base_dir value is a resolved absolute path."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        settings = Settings(
            google_api_key="test-key",
            base_url="https://example.com",
            vault_base_dir=str(vault_base),
            vault_output_dir=str(vault_output),
            dashboard_password_hash=TEST_HASH,
            session_secret_key="test-secret",
        )
        resolved = str(Path(vault_base).resolve())
        assert settings.vault_base_dir == resolved

    def test_vault_output_dir_outside_base_raises(self, tmp_path) -> None:
        """VAULT_OUTPUT_DIR outside VAULT_BASE_DIR raises ValidationError."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        with pytest.raises(
            ValidationError, match="VAULT_OUTPUT_DIR must be within VAULT_BASE_DIR"
        ):
            Settings(
                google_api_key="test-key",
                base_url="https://example.com",
                vault_base_dir=str(vault_base),
                vault_output_dir=str(other_dir),
                dashboard_password_hash=TEST_HASH,
                session_secret_key="test-secret",
            )

    def test_vault_output_dir_within_base_succeeds(self, tmp_path) -> None:
        """Valid nested VAULT_OUTPUT_DIR is accepted."""
        vault_base = tmp_path / "vault_base"
        vault_base.mkdir()
        vault_output = vault_base / "output"
        vault_output.mkdir()
        settings = Settings(
            google_api_key="test-key",
            base_url="https://example.com",
            vault_base_dir=str(vault_base),
            vault_output_dir=str(vault_output),
            dashboard_password_hash=TEST_HASH,
            session_secret_key="test-secret",
        )
        assert settings.vault_base_dir == str(vault_base.resolve())


class TestEnvExample:
    def test_env_example_has_all_settings_fields(self) -> None:
        """Verify .env.example documents every required Settings field."""
        env_example = open("D:/Podcast Workflow/.env.example").read()
        required_vars = [
            "GOOGLE_API_KEY",
            "BASE_URL",
            "VAULT_BASE_DIR",
            "VAULT_OUTPUT_DIR",
            "DASHBOARD_PASSWORD_HASH",
            "SESSION_SECRET_KEY",
        ]
        for var in required_vars:
            assert var in env_example, f"Missing required var {var} in .env.example"
