"""Config-driven prompt builder for podcast script generation."""

from src.domain.models import Host, Style


def build_script_prompt(content: str, hosts: list[Host], style: Style) -> str:
    """Build a prompt for the LLM to generate a podcast script.

    Dynamically incorporates host names, roles, style tone, and optional
    personality guidance. Produces a free-flowing conversation format.

    Args:
        content: Sanitized source material for the podcast episode.
        hosts: Exactly two Host objects defining speakers.
        style: Style object controlling tone and personality.

    Returns:
        Complete prompt string for the script-generation LLM.
    """
    host_a, host_b = hosts[0], hosts[1]

    parts: list[str] = [
        f"Create a lively, engaging podcast conversation between {host_a.name} "
        f"({host_a.role}) and {host_b.name} ({host_b.role}), "
        f"discussing the following content.",
        f"Tone: {style.tone}.",
        "Make it feel like a real conversation: "
        "they ask each other questions, build on each other's points, occasionally joke around, "
        "express genuine excitement or surprise when something is interesting, and push back "
        "or ask for clarification when something is unclear. "
        "Vary the energy \u2014 some moments are thoughtful and serious, others are lighter. "
        "Do NOT just take turns summarizing \u2014 make it a real back-and-forth.",
    ]

    if style.personality_guidance is not None:
        parts.append(f"Additional guidance: {style.personality_guidance}")

    parts.append(
        f"Output ONLY the script. Format strictly as:\n"
        f"{host_a.name}: ...\n"
        f"{host_b.name}: ..."
    )

    parts.append(f"Content:\n{content}")

    return "\n\n".join(parts)
