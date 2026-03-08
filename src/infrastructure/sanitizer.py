"""Sanitize Obsidian markdown for TTS consumption.

Strips non-speakable elements (code blocks, math, metadata, formatting markers)
while preserving readable text content. Pattern application order is critical
to prevent interference between overlapping syntax.
"""

import re

# Pre-compiled patterns in application order.
# Compiling once avoids re-compilation on every call.

_OBSIDIAN_COMMENT = re.compile(r"%%.*?%%", re.DOTALL)
_YAML_FRONTMATTER = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)
_FENCED_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_DISPLAY_MATH = re.compile(r"\$\$.*?\$\$", re.DOTALL)
_INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)(?!\d)(.+?)(?<!\$)\$(?!\$)")
_OBSIDIAN_EMBED = re.compile(r"!\[\[.*?\]\]")
_CALLOUT_HEADER = re.compile(r"^> \[![\w-]+\][-+]?[^\S\n]*.*$", re.MULTILINE)
_CALLOUT_BODY_PREFIX = re.compile(r"^> ", re.MULTILINE)
_MARKDOWN_TABLE = re.compile(r"(^\|.+\n){2,}", re.MULTILINE)
_FOOTNOTE_DEFINITION = re.compile(r"^\[\^\w+\]:.*$\n?", re.MULTILINE)
_FOOTNOTE_REFERENCE = re.compile(r"\[\^\w+\]")
_HIGHLIGHT = re.compile(r"==(.+?)==")
_STRIKETHROUGH = re.compile(r"~~.*?~~")
_TAG = re.compile(r"(?<!\w)#[\w][\w/-]*")
_BLOCK_ID = re.compile(r"\s*\^[\w-]+\s*$", re.MULTILINE)
_WIKI_LINK_DISPLAY = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")
_WIKI_LINK_PLAIN = re.compile(r"\[\[([^\]]+)\]\]")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")


def sanitize_markdown(text: str) -> str:
    """Strip non-speakable markdown elements before passing to TTS.

    Processes patterns in a specific order to prevent interference
    between overlapping Obsidian/Markdown syntax constructs.

    Args:
        text: Raw Obsidian markdown content.

    Returns:
        Cleaned text suitable for TTS input.
    """
    # a. Obsidian comments %%...%% (must be first to prevent partial matches)
    text = _OBSIDIAN_COMMENT.sub("", text)

    # b. YAML front-matter
    text = _YAML_FRONTMATTER.sub("", text)

    # c. Fenced code blocks (catches mermaid, dataview, etc.)
    text = _FENCED_CODE_BLOCK.sub("", text)

    # d. Display math $$...$$
    text = _DISPLAY_MATH.sub("", text)

    # e. Inline math $...$
    text = _INLINE_MATH.sub("", text)

    # f. Obsidian embeds ![[...]]
    text = _OBSIDIAN_EMBED.sub("", text)

    # g. Callout headers > [!type]
    text = _CALLOUT_HEADER.sub("", text)

    # h. Callout body markers: strip leading "> " from remaining lines
    text = _CALLOUT_BODY_PREFIX.sub("", text)

    # i. Markdown tables
    text = _MARKDOWN_TABLE.sub("", text)

    # j. Footnote definitions (full line)
    text = _FOOTNOTE_DEFINITION.sub("", text)

    # k. Footnote references (inline)
    text = _FOOTNOTE_REFERENCE.sub("", text)

    # l. Highlights ==text== -> text
    text = _HIGHLIGHT.sub(r"\1", text)

    # m. Strikethrough ~~text~~
    text = _STRIKETHROUGH.sub("", text)

    # n. Tags (must not match headings: lookbehind ensures # is not preceded by word char)
    text = _TAG.sub("", text)

    # o. Block IDs ^block-id at end of line
    text = _BLOCK_ID.sub("", text)

    # p. Wiki links
    text = _WIKI_LINK_DISPLAY.sub(r"\2", text)
    text = _WIKI_LINK_PLAIN.sub(r"\1", text)

    # q. Inline code backticks — keep text, drop backticks
    text = _INLINE_CODE.sub(r"\1", text)

    # r. Collapse 3+ blank lines into 2
    text = _EXCESS_BLANK_LINES.sub("\n\n", text)

    return text.strip()
