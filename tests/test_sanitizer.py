"""Tests for Obsidian markdown sanitizer."""

import pytest

from src.infrastructure.sanitizer import sanitize_markdown


# --- Existing behavior tests ---


class TestYamlFrontmatter:
    def test_strips_yaml_frontmatter(self) -> None:
        text = "---\ntitle: My Note\ntags: [a, b]\n---\nActual content here."
        assert sanitize_markdown(text) == "Actual content here."


class TestFencedCodeBlocks:
    def test_strips_fenced_code_blocks(self) -> None:
        text = "Before code.\n```python\ndef foo():\n    pass\n```\nAfter code."
        assert sanitize_markdown(text) == "Before code.\n\nAfter code."

    def test_strips_mermaid_blocks(self) -> None:
        text = "Before.\n```mermaid\ngraph TD\nA-->B\n```\nAfter."
        assert sanitize_markdown(text) == "Before.\n\nAfter."

    def test_strips_dataview_blocks(self) -> None:
        text = "Before.\n```dataview\nTABLE file.name\n```\nAfter."
        assert sanitize_markdown(text) == "Before.\n\nAfter."


class TestMarkdownTables:
    def test_strips_markdown_tables(self) -> None:
        text = "Before table.\n| Col1 | Col2 |\n| --- | --- |\n| a | b |\nAfter table."
        assert sanitize_markdown(text) == "Before table.\nAfter table."


class TestWikiLinks:
    def test_converts_wiki_links_with_display(self) -> None:
        text = "See [[Some Page|this page]] for details."
        assert sanitize_markdown(text) == "See this page for details."

    def test_converts_wiki_links_plain(self) -> None:
        text = "See [[Some Page]] for details."
        assert sanitize_markdown(text) == "See Some Page for details."


class TestInlineCode:
    def test_strips_inline_code_backticks(self) -> None:
        text = "Use `print()` to output."
        assert sanitize_markdown(text) == "Use print() to output."


# --- New Obsidian-specific pattern tests ---


class TestObsidianComments:
    def test_strips_obsidian_comments(self) -> None:
        text = "Visible text. %%This is a comment.%% More visible."
        assert sanitize_markdown(text) == "Visible text.  More visible."

    def test_strips_multiline_comments(self) -> None:
        text = "Before.\n%%\nThis is a\nmultiline comment.\n%%\nAfter."
        assert sanitize_markdown(text) == "Before.\n\nAfter."


class TestMath:
    def test_strips_display_math(self) -> None:
        text = "Before math.\n$$\nE = mc^2\n$$\nAfter math."
        assert sanitize_markdown(text) == "Before math.\n\nAfter math."

    def test_strips_inline_math(self) -> None:
        text = "The formula $E = mc^2$ is famous."
        assert sanitize_markdown(text) == "The formula  is famous."

    def test_inline_math_does_not_match_dollar_amounts(self) -> None:
        text = "Price is $50 and cost is $100 total."
        assert sanitize_markdown(text) == "Price is $50 and cost is $100 total."


class TestObsidianEmbeds:
    def test_strips_obsidian_embeds(self) -> None:
        text = "See this image: ![[screenshot.png]]\nAnd this: ![[other note]]"
        result = sanitize_markdown(text)
        assert "![[" not in result
        assert "See this image:" in result
        assert "And this:" in result

    def test_strips_embed_at_line_start(self) -> None:
        text = "![[embedded-note]]\nNext line."
        assert sanitize_markdown(text) == "Next line."


class TestCallouts:
    def test_strips_callout_header_keeps_body(self) -> None:
        text = "> [!note]\n> This is the callout body.\n> Second line."
        assert sanitize_markdown(text) == "This is the callout body.\nSecond line."

    def test_strips_callout_header_types(self) -> None:
        for callout_type in ("warning", "tip", "info"):
            text = f"> [!{callout_type}]\n> Body content here."
            result = sanitize_markdown(text)
            assert result == "Body content here.", (
                f"Failed for callout type: {callout_type}"
            )

    def test_strips_callout_header_with_title(self) -> None:
        text = "> [!warning] Be careful\n> Important details here."
        assert sanitize_markdown(text) == "Important details here."

    def test_strips_foldable_callout(self) -> None:
        text = "> [!note]+\n> Expanded by default."
        assert sanitize_markdown(text) == "Expanded by default."

    def test_strips_collapsed_callout(self) -> None:
        text = "> [!note]-\n> Collapsed by default."
        assert sanitize_markdown(text) == "Collapsed by default."


class TestHighlights:
    def test_strips_highlights_keeps_text(self) -> None:
        text = "This is ==very important== information."
        assert sanitize_markdown(text) == "This is very important information."


class TestStrikethrough:
    def test_strips_strikethrough(self) -> None:
        text = "This is ~~deleted~~ text."
        assert sanitize_markdown(text) == "This is  text."


class TestTags:
    def test_strips_tags(self) -> None:
        text = "Some text #tag and #another-tag here."
        assert sanitize_markdown(text) == "Some text  and  here."

    def test_strips_nested_tags(self) -> None:
        text = "Tagged with #project/subtask value."
        assert sanitize_markdown(text) == "Tagged with  value."

    def test_preserves_headings_not_tags(self) -> None:
        text = "# Heading One\n## Heading Two\n### Heading Three"
        assert sanitize_markdown(text) == "# Heading One\n## Heading Two\n### Heading Three"


class TestBlockIds:
    def test_strips_block_ids(self) -> None:
        text = "This is a paragraph. ^block-id-123\nNext line."
        assert sanitize_markdown(text) == "This is a paragraph.\nNext line."


class TestFootnotes:
    def test_strips_footnote_references(self) -> None:
        text = "Some claim[^1] and another[^note] here."
        assert sanitize_markdown(text) == "Some claim and another here."

    def test_strips_footnote_definitions(self) -> None:
        text = "Main text here.\n[^1]: This is the footnote content.\nMore text."
        assert sanitize_markdown(text) == "Main text here.\nMore text."


class TestBlankLineCollapse:
    def test_collapses_excessive_blank_lines(self) -> None:
        text = "Line one.\n\n\n\n\nLine two."
        assert sanitize_markdown(text) == "Line one.\n\nLine two."


# --- Integration test ---


class TestCombinedObsidianContent:
    def test_combined_obsidian_content(self) -> None:
        text = (
            "---\n"
            "title: Test Note\n"
            "tags: [review]\n"
            "---\n"
            "\n"
            "# Introduction\n"
            "\n"
            "%% Author note: draft version %%\n"
            "\n"
            "This is ==highlighted text== with a [[wiki link|link]] "
            "and a #topic tag.\n"
            "\n"
            "$$\n"
            "x = \\frac{-b}{2a}\n"
            "$$\n"
            "\n"
            "> [!tip] Pro tip\n"
            "> Remember to review the $E = mc^2$ formula.\n"
            "> Second line of the callout.\n"
            "\n"
            "Some text with ~~strikethrough~~ and `inline code` here.\n"
            "\n"
            "![[embedded-note]]\n"
            "\n"
            "Footnote reference[^1] in text. ^block-ref\n"
            "\n"
            "[^1]: This is the footnote definition.\n"
            "\n"
            "```python\n"
            "print('hello')\n"
            "```\n"
            "\n"
            "| Col | Val |\n"
            "| --- | --- |\n"
            "| a   | b   |\n"
            "\n"
            "Final paragraph.\n"
        )
        result = sanitize_markdown(text)

        # Should preserve
        assert "# Introduction" in result
        assert "highlighted text" in result
        assert "link" in result
        assert "Remember to review the" in result
        assert "Second line of the callout" in result
        assert "inline code" in result
        assert "Final paragraph." in result

        # Should strip
        assert "%%" not in result
        assert "title: Test Note" not in result
        assert "$$" not in result
        assert "```" not in result
        assert "==" not in result
        assert "~~" not in result
        assert "![[" not in result
        assert "[^1]" not in result
        assert "^block-ref" not in result
        assert "#topic" not in result
        assert "> [!tip]" not in result
        assert "| Col" not in result
