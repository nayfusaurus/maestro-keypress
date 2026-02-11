"""Tests for Heartopia 15-key double row keymap."""

import pytest
from maestro.keymap_15_double import midi_note_to_key_15_double


class TestMidRowMappings:
    """Test mid row natural notes (C4-B4, MIDI 60-71)."""

    @pytest.mark.parametrize(
        "note,key",
        [
            (60, "a"),  # C4
            (62, "s"),  # D4
            (64, "d"),  # E4
            (65, "f"),  # F4
            (67, "g"),  # G4
            (69, "h"),  # A4
            (71, "j"),  # B4
        ],
    )
    def test_mid_row_natural_mappings(self, note, key):
        """Mid row natural notes should map to A-J keys."""
        assert midi_note_to_key_15_double(note) == key


class TestHighRowMappings:
    """Test high row natural notes (C5-C6, MIDI 72-84)."""

    @pytest.mark.parametrize(
        "note,key",
        [
            (72, "q"),  # C5
            (74, "w"),  # D5
            (76, "e"),  # E5
            (77, "r"),  # F5
            (79, "t"),  # G5
            (81, "y"),  # A5
            (83, "u"),  # B5
            (84, "i"),  # C6
        ],
    )
    def test_high_row_natural_mappings(self, note, key):
        """High row natural notes should map to Q-I keys."""
        assert midi_note_to_key_15_double(note) == key


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
        assert midi_note_to_key_15_double(note) is None


class TestSharpSnapMode:
    """Test sharp notes snap to nearest natural in snap mode."""

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (61, "a"),  # C#4 → C4
            (63, "s"),  # D#4 → D4
            (66, "f"),  # F#4 → F4
            (68, "g"),  # G#4 → G4
            (70, "h"),  # A#4 → A4
            (73, "q"),  # C#5 → C5
            (75, "w"),  # D#5 → D5
            (78, "r"),  # F#5 → F5
            (80, "t"),  # G#5 → G5
            (82, "y"),  # A#5 → A5
        ],
    )
    def test_sharp_notes_snap_to_nearest_natural(self, note, expected_key):
        """Sharp notes should snap to nearest natural in snap mode."""
        assert midi_note_to_key_15_double(note, sharp_handling="snap") == expected_key


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN (60) should be valid."""
        assert midi_note_to_key_15_double(60) == "a"

    def test_max_note_boundary(self):
        """Note at MAX (84) should be valid."""
        assert midi_note_to_key_15_double(84) == "i"

    def test_note_below_min_is_invalid(self):
        """Note below MIN (59) should return None."""
        assert midi_note_to_key_15_double(59) is None


class TestTranspose:
    """Test transpose behavior for out-of-range notes."""

    def test_transpose_below_into_range(self):
        """C3 (MIDI 48) should transpose up to C4."""
        assert midi_note_to_key_15_double(48, transpose=True) == "a"

    def test_transpose_above_into_range(self):
        """C7 (MIDI 96) should transpose down to C6."""
        assert midi_note_to_key_15_double(96, transpose=True) == "i"

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not be affected by transpose."""
        assert midi_note_to_key_15_double(60, transpose=True) == "a"
        assert midi_note_to_key_15_double(72, transpose=True) == "q"

    def test_transpose_sharp_with_snap_mode(self):
        """C#3 (MIDI 49) transposes to C#4, snap mode returns C4."""
        assert (
            midi_note_to_key_15_double(49, transpose=True, sharp_handling="snap") == "a"
        )


class TestOutOfRange:
    """Test out-of-range notes return None when transpose=False."""

    def test_note_below_range(self):
        """MIDI 36 (C2) is below range, should return None."""
        assert midi_note_to_key_15_double(36) is None

    def test_note_above_range(self):
        """MIDI 96 (C7) is above range, should return None."""
        assert midi_note_to_key_15_double(96) is None
