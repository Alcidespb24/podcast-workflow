"""RSS feed generation and validation for podcast distribution."""

import xml.etree.ElementTree as ET
from datetime import timezone

from feedgen.feed import FeedGenerator

from src.domain.models import Episode
from src.exceptions import RSSError

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"

_REQUIRED_ITUNES_TAGS = ("author", "explicit", "category")


def build_podcast_feed(
    podcast_title: str,
    podcast_description: str,
    base_url: str,
    episodes: list[Episode],
    *,
    email: str = "",
    cover_url: str = "",
) -> str:
    """Build a complete RSS feed XML string from episode data.

    Uses feedgen with the podcast extension to produce an iTunes-compatible
    RSS feed. Enclosure URLs are constructed as {base_url}/episodes/{filename}.

    Args:
        podcast_title: Name of the podcast (channel title).
        podcast_description: Channel-level description.
        base_url: Public base URL for episode file serving.
        episodes: List of Episode domain objects to include as items.

    Returns:
        Pretty-printed RSS XML string.

    Raises:
        RSSError: If feed generation fails for any reason.
    """
    try:
        fg = FeedGenerator()
        fg.load_extension("podcast")

        # Channel-level fields
        fg.title(podcast_title)
        fg.link(href=base_url, rel="alternate")
        fg.description(podcast_description)
        fg.language("en")

        # Owner / contact
        if email:
            fg.podcast.itunes_owner(name=podcast_title, email=email)
            fg.managingEditor(email)
        if cover_url:
            fg.podcast.itunes_image(cover_url)
            fg.image(url=cover_url, title=podcast_title, link=base_url)

        # iTunes namespace fields
        fg.podcast.itunes_author(podcast_title)
        fg.podcast.itunes_explicit("no")
        fg.podcast.itunes_category("Technology")
        fg.podcast.itunes_type("episodic")

        # Episode entries
        for ep in episodes:
            entry = fg.add_entry()
            enclosure_url = f"{base_url}/episodes/{ep.filename}"

            entry.id(enclosure_url)
            entry.title(ep.title)
            entry.description(ep.description)
            pub_at = ep.published_at
            if pub_at and pub_at.tzinfo is None:
                pub_at = pub_at.replace(tzinfo=timezone.utc)
            entry.published(pub_at)
            entry.enclosure(enclosure_url, str(ep.file_size), "audio/mpeg")

            entry.podcast.itunes_duration(ep.duration_str)
            entry.podcast.itunes_episode(ep.episode_number)
            entry.podcast.itunes_episode_type("full")

        return fg.rss_str(pretty=True).decode("utf-8")
    except Exception as exc:
        raise RSSError(f"Failed to generate RSS feed: {exc}") from exc


def validate_podcast_rss(xml_str: str) -> list[str]:
    """Validate an RSS XML string for required podcast fields.

    Checks for:
    - Presence of <channel> element
    - Required iTunes namespace tags at channel level (author, explicit, category)
    - Required per-item elements (title, enclosure, guid)

    Args:
        xml_str: RSS feed XML as a string.

    Returns:
        List of error strings. Empty list means the feed is valid.
    """
    errors: list[str] = []

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        return [f"Invalid XML: {exc}"]

    channel = root.find("channel")
    if channel is None:
        return ["Missing required <channel> element"]

    # Check required iTunes namespace tags
    for tag in _REQUIRED_ITUNES_TAGS:
        if channel.find(f"{{{ITUNES_NS}}}{tag}") is None:
            errors.append(f"Missing required iTunes tag: itunes:{tag}")

    # Check each item for required fields
    for i, item in enumerate(channel.findall("item")):
        item_label = f"item[{i}]"
        if item.find("title") is None:
            errors.append(f"{item_label}: missing <title>")
        if item.find("enclosure") is None:
            errors.append(f"{item_label}: missing <enclosure>")
        if item.find("guid") is None:
            errors.append(f"{item_label}: missing <guid>")

    return errors
