"""Tests for the speaker-turn-aware script chunker and speaker validation."""

from src.infrastructure.chunker import chunk_script, normalize_speakers, validate_speakers


class TestChunkScript:
    def test_chunk_script_single_chunk(self) -> None:
        script = "Joe: Hello there!\nJane: Hi Joe!"
        chunks = chunk_script(script, ["Joe", "Jane"], max_chars=5000)
        assert len(chunks) == 1
        assert chunks[0] == script

    def test_chunk_script_splits_at_speaker_turns(self) -> None:
        turn_a = "Joe: " + "A" * 100
        turn_b = "Jane: " + "B" * 100
        turn_c = "Joe: " + "C" * 100
        script = f"{turn_a}\n{turn_b}\n{turn_c}"
        chunks = chunk_script(script, ["Joe", "Jane"], max_chars=250)
        assert len(chunks) >= 2
        # Each chunk should start with a valid speaker turn
        for chunk in chunks:
            assert chunk.startswith("Joe:") or chunk.startswith("Jane:")

    def test_chunk_script_respects_max_chars(self) -> None:
        turns = []
        for i in range(20):
            name = "Joe" if i % 2 == 0 else "Jane"
            turns.append(f"{name}: {'X' * 200}")
        script = "\n".join(turns)
        max_chars = 500
        chunks = chunk_script(script, ["Joe", "Jane"], max_chars=max_chars)
        for chunk in chunks:
            assert len(chunk) <= max_chars or "\n" not in chunk  # single oversized turn allowed

    def test_chunk_script_preserves_all_content(self) -> None:
        turns = [
            "Joe: First point here.",
            "Jane: Good point Joe.",
            "Joe: Let me elaborate.",
            "Jane: Please do.",
        ]
        script = "\n".join(turns)
        chunks = chunk_script(script, ["Joe", "Jane"], max_chars=60)
        reassembled = "\n".join(chunks)
        for turn in turns:
            assert turn in reassembled

    def test_chunk_script_sentence_fallback(self) -> None:
        """Single turn exceeding max_chars is split at sentence boundaries."""
        long_turn = "Joe: First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_script(long_turn, ["Joe", "Jane"], max_chars=40)
        assert len(chunks) >= 2
        # Reassembled content should preserve all sentences
        joined = " ".join(chunks)
        assert "First sentence" in joined
        assert "Fourth sentence" in joined


class TestValidateSpeakers:
    def test_validate_speakers_valid(self) -> None:
        script = "Joe: Hello\nJane: Hi\nJoe: How are you?"
        valid, unexpected = validate_speakers(script, ["Joe", "Jane"])
        assert valid is True
        assert unexpected == set()

    def test_validate_speakers_invalid(self) -> None:
        script = "Joe: Hello\nBob: Hi there"
        valid, unexpected = validate_speakers(script, ["Joe", "Jane"])
        assert valid is False
        assert "Bob" in unexpected

    def test_validate_speakers_case_sensitive(self) -> None:
        script = "joe: Hello\nJane: Hi"
        valid, unexpected = validate_speakers(script, ["Joe", "Jane"])
        assert valid is False
        assert "joe" in unexpected


class TestNormalizeSpeakers:
    def test_normalize_speakers_fixes_case(self) -> None:
        script = "joe: Hello there\njane: Hi"
        result = normalize_speakers(script, ["Joe", "Jane"])
        assert "Joe: Hello there" in result
        assert "Jane: Hi" in result

    def test_normalize_speakers_no_change_needed(self) -> None:
        script = "Joe: Hello\nJane: Hi"
        result = normalize_speakers(script, ["Joe", "Jane"])
        assert result == script
