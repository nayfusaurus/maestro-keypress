"""Tests for Heartopia 15-key triple row keymap."""

import pytest
from maestro.keymap_15_triple import midi_note_to_key_15_triple


class TestNaturalNoteMappings:
    """Test all 15 natural notes map correctly (C4-C6, MIDI 60-84)."""

    @pytest.mark.parametrize(
        "note,key",
        [
            # Row 1: YUIOP
            (60, "y"),  # C4
            (62, "u"),  # D4
            (64, "i"),  # E4
            (65, "o"),  # F4
            (67, "p"),  # G4
            # Row 2: HJKLsemicolon
            (69, "h"),  # A4
            (71, "j"),  # B4
            (72, "k"),  # C5
            (74, "l"),  # D5
            (76, ";"),  # E5
            # Row 3: NM,./
            (77, "n"),  # F5
            (79, "m"),  # G5
            (81, ","),  # A5
            (83, "."),  # B5
            (84, "/"),  # C6
        ],
    )
    def test_natural_note_mappings(self, note, key):
        """All 15 natural notes should map to correct keys."""
        assert midi_note_to_key_15_triple(note) == key


class TestSharpSkipMode:
    """Test sharp notes return None with default skip mode."""

    @pytest.mark.parametrize(
        "note",
        [
            61,  # C#4
            63,  # D#4
            66,  # F#4
            68,  # G#4
            70,  # A#4
            73,  # C#5
            75,  # D#5
            78,  # F#5
            80,  # G#5
            82,  # A#5
        ],
    )
    def test_sharp_notes_return_none_in_skip_mode(self, note):
        """Sharp notes should return None in default skip mode."""
        assert midi_note_to_key_15_triple(note) is None


class TestSharpSnapMode:
    """Test sharp notes snap to nearest natural in snap mode."""

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (61, "y"),  # C#4 → C4
            (63, "u"),  # D#4 → D4
            (66, "o"),  # F#4 → F4
            (68, "p"),  # G#4 → G4
            (70, "h"),  # A#4 → A4
            (73, "k"),  # C#5 → C5
            (75, "l"),  # D#5 → D5
            (78, "n"),  # F#5 → F5
            (80, "m"),  # G#5 → G5
            (82, ","),  # A#5 → A5
        ],
    )
    def test_sharp_notes_snap_to_nearest_natural(self, note, expected_key):
        """Sharp notes should snap to nearest natural in snap mode."""
        assert midi_note_to_key_15_triple(note, sharp_handling="snap") == expected_key


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN (60) should be valid."""
        assert midi_note_to_key_15_triple(60) == "y"

    def test_max_note_boundary(self):
        """Note at MAX (84) should be valid."""
        assert midi_note_to_key_15_triple(84) == "/"

    def test_note_below_min_is_invalid(self):
        """Note below MIN (59) should return None."""
        assert midi_note_to_key_15_triple(59) is None


class TestTranspose:
    """Test transpose behavior for out-of-range notes."""

    def test_transpose_below_into_range(self):
        """C3 (MIDI 48) should transpose up to C4."""
        assert midi_note_to_key_15_triple(48, transpose=True) == "y"

    def test_transpose_above_into_range(self):
        """C7 (MIDI 96) should transpose down to C6."""
        assert midi_note_to_key_15_triple(96, transpose=True) == "/"

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not be affected by transpose."""
        assert midi_note_to_key_15_triple(60, transpose=True) == "y"
        assert midi_note_to_key_15_triple(72, transpose=True) == "k"

    def test_transpose_sharp_with_snap_mode(self):
        """C#3 (MIDI 49) transposes to C#4, snap mode returns C4."""
        assert (
            midi_note_to_key_15_triple(49, transpose=True, sharp_handling="snap") == "y"
        )


class TestOutOfRange:
    """Test out-of-range notes return None when transpose=False."""

    def test_note_below_range(self):
        """MIDI 36 (C2) is below range, should return None."""
        assert midi_note_to_key_15_triple(36) is None

    def test_note_above_range(self):
        """MIDI 96 (C7) is above range, should return None."""
        assert midi_note_to_key_15_triple(96) is None
