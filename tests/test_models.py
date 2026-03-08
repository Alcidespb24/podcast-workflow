import pytest

from src.domain.models import Host, PipelineConfig, Style


class TestHost:
    def test_host_creation(self) -> None:
        host = Host(name="Joe", voice="Kore", role="host")
        assert host.name == "Joe"
        assert host.voice == "Kore"
        assert host.role == "host"

    def test_host_default_role(self) -> None:
        host = Host(name="Joe", voice="Kore")
        assert host.role == "host"


class TestStyle:
    def test_style_creation(self) -> None:
        style = Style(name="Default", tone="Informative & engaging")
        assert style.name == "Default"
        assert style.tone == "Informative & engaging"

    def test_style_speaker_count_locked_to_two(self) -> None:
        style = Style(name="Default", tone="Casual")
        assert style.speaker_count == 2

    def test_style_speaker_count_rejects_one(self) -> None:
        with pytest.raises(ValueError):
            Style(name="Default", tone="Casual", speaker_count=1)

    def test_style_personality_guidance_optional(self) -> None:
        style = Style(name="Default", tone="Casual")
        assert style.personality_guidance is None

        style_with_guidance = Style(
            name="Custom",
            tone="Serious",
            personality_guidance="Be formal and academic",
        )
        assert style_with_guidance.personality_guidance == "Be formal and academic"


class TestPipelineConfig:
    def test_pipeline_config_valid(self) -> None:
        hosts = [
            Host(name="Joe", voice="Kore", role="host"),
            Host(name="Jane", voice="Puck", role="co-host"),
        ]
        style = Style(name="Default", tone="Casual")
        config = PipelineConfig(
            hosts=hosts, style=style, source_file="notes.md"
        )
        assert len(config.hosts) == 2
        assert config.source_file == "notes.md"

    def test_pipeline_config_rejects_one_host(self) -> None:
        hosts = [Host(name="Joe", voice="Kore")]
        style = Style(name="Default", tone="Casual")
        with pytest.raises(ValueError, match="Exactly 2 hosts required"):
            PipelineConfig(hosts=hosts, style=style, source_file="notes.md")

    def test_pipeline_config_rejects_three_hosts(self) -> None:
        hosts = [
            Host(name="Joe", voice="Kore"),
            Host(name="Jane", voice="Puck"),
            Host(name="Bob", voice="Sage"),
        ]
        style = Style(name="Default", tone="Casual")
        with pytest.raises(ValueError, match="Exactly 2 hosts required"):
            PipelineConfig(hosts=hosts, style=style, source_file="notes.md")

    def test_pipeline_config_rejects_zero_hosts(self) -> None:
        style = Style(name="Default", tone="Casual")
        with pytest.raises(ValueError, match="Exactly 2 hosts required"):
            PipelineConfig(hosts=[], style=style, source_file="notes.md")
