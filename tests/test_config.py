from src.config import Settings


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
        )
        settings = Settings(_env_file=env_file)
        assert settings.database_url == "sqlite:///data/podcast.db"

    def test_settings_default_hosts(self, tmp_path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_API_KEY=test-key\n"
            "BASE_URL=https://example.com\n"
            "VAULT_OUTPUT_DIR=/tmp/vault\n"
        )
        settings = Settings(_env_file=env_file)
        assert isinstance(settings.default_host_a_name, str)
        assert isinstance(settings.default_host_a_voice, str)
        assert isinstance(settings.default_host_b_name, str)
        assert isinstance(settings.default_host_b_voice, str)
