"""Tests for application settings and startup validation."""

import sys

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
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            "VAULT_OUTPUT_DIR=/tmp/vault\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
        )
        settings = Settings(_env_file=env_file)
        assert settings.database_url == "sqlite:///data/podcast.db"

    def test_settings_default_hosts(self, tmp_path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            "VAULT_OUTPUT_DIR=/tmp/vault\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
        )
        settings = Settings(_env_file=env_file)
        assert isinstance(settings.default_host_a_name, str)
        assert isinstance(settings.default_host_a_voice, str)
        assert isinstance(settings.default_host_b_name, str)
        assert isinstance(settings.default_host_b_voice, str)


class TestStartupValidation:
    def test_missing_password_hash_raises(self, tmp_path) -> None:
        """Settings rejects instantiation when DASHBOARD_PASSWORD_HASH is missing."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            "VAULT_OUTPUT_DIR=/tmp/vault\n"
        )
        with pytest.raises(ValidationError):
            Settings(_env_file=env_file)

    def test_malformed_password_hash_raises(self) -> None:
        """Settings rejects a DASHBOARD_PASSWORD_HASH that is not Argon2id."""
        with pytest.raises(ValidationError, match="Argon2id"):
            Settings(
                google_api_key="test-key",
                base_url="https://example.com",
                vault_output_dir="/tmp/vault",
                REDACTED_FIELD_hash="not-a-hash",
            )

    def test_valid_argon2id_hash_accepted(self) -> None:
        """Settings accepts a valid Argon2id hash string."""
        settings = Settings(
            google_api_key="test-key",
            base_url="https://example.com",
            vault_output_dir="/tmp/vault",
            REDACTED_FIELD_hash=TEST_HASH,
        )
        assert settings.REDACTED_FIELD_hash == TEST_HASH

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

    def test_load_settings_returns_settings_on_valid_config(self, tmp_path) -> None:
        """load_settings() returns a Settings instance when config is valid."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            "VAULT_OUTPUT_DIR=/tmp/vault\n"
            f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
        )
        settings = load_settings(_env_file=env_file)
        assert isinstance(settings, Settings)
        assert settings.google_api_key == "test-key"


class TestEnvExample:
    def test_env_example_has_all_settings_fields(self) -> None:
        """Verify .env.example documents every required Settings field."""
        env_example = open("D:/Podcast Workflow/.env.example").read()
        required_vars = [
            "GOOGLE_API_KEY",
            "BASE_URL",
            "VAULT_OUTPUT_DIR",
            "DASHBOARD_PASSWORD_HASH",
        ]
        for var in required_vars:
            assert var in env_example, f"Missing required var {var} in .env.example"
