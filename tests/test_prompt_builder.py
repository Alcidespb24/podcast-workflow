"""Tests for the config-driven prompt builder."""

from src.domain.models import Host, Style
from src.domain.prompt_builder import build_script_prompt


def _make_hosts(name_a: str = "Joe", name_b: str = "Jane") -> list[Host]:
    return [
        Host(name=name_a, voice="Kore", role="host"),
        Host(name=name_b, voice="Puck", role="co-host"),
    ]


def _make_style(
    tone: str = "Informative & engaging",
    personality_guidance: str | None = None,
) -> Style:
    return Style(name="Default", tone=tone, personality_guidance=personality_guidance)


class TestBuildScriptPrompt:
    def test_prompt_includes_host_names(self) -> None:
        hosts = _make_hosts("Alice", "Bob")
        prompt = build_script_prompt("content", hosts, _make_style())
        assert "Alice" in prompt
        assert "Bob" in prompt

    def test_prompt_includes_host_roles(self) -> None:
        hosts = _make_hosts()
        prompt = build_script_prompt("content", hosts, _make_style())
        assert "host" in prompt.lower()
        assert "co-host" in prompt.lower()

    def test_prompt_includes_style_tone(self) -> None:
        style = _make_style(tone="Casual & humorous")
        prompt = build_script_prompt("content", _make_hosts(), style)
        assert "Casual & humorous" in prompt

    def test_prompt_includes_personality_guidance_when_set(self) -> None:
        style = _make_style(personality_guidance="Be sarcastic and witty")
        prompt = build_script_prompt("content", _make_hosts(), style)
        assert "Be sarcastic and witty" in prompt

    def test_prompt_omits_personality_guidance_when_none(self) -> None:
        style = _make_style(personality_guidance=None)
        prompt = build_script_prompt("content", _make_hosts(), style)
        assert "None" not in prompt
        assert "personality" not in prompt.lower()

    def test_prompt_includes_content(self) -> None:
        prompt = build_script_prompt("My source material", _make_hosts(), _make_style())
        assert "My source material" in prompt

    def test_prompt_specifies_output_format(self) -> None:
        hosts = _make_hosts("Alice", "Bob")
        prompt = build_script_prompt("content", hosts, _make_style())
        assert "Alice:" in prompt
        assert "Bob:" in prompt
        assert "Format strictly as" in prompt or "Format" in prompt
