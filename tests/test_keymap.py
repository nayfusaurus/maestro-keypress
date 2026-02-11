"""Tests for Heartopia 22-key keymap (C3-C6)."""

import pytest
from maestro.keymap import midi_note_to_key


class TestNoteMappings:
    """Test key note mappings across all octaves."""

    @pytest.mark.parametrize(
        "note,key,description",
        [
            (48, ",", "C3 - low octave"),
            (54, "0", "F#3 - low octave black key"),
            (56, "-", "G#3 - low octave black key"),
            (60, "z", "C4 - middle C"),
            (61, "s", "C#4 - mid octave black key"),
            (72, "q", "C5 - high octave"),
            (84, "i", "C6 - extended high"),
        ],
    )
    def test_note_mappings(self, note, key, description):
        """All notes should map to correct keys across octaves."""
        assert midi_note_to_key(note) == key


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN (48) should be valid."""
        assert midi_note_to_key(48) == ","

    def test_max_note_boundary(self):
        """Note at MAX (84) should be valid."""
        assert midi_note_to_key(84) == "i"

    def test_note_below_min_is_invalid(self):
        """Note below MIN (47) should return None."""
        assert midi_note_to_key(47) is None


class TestTranspose:
    """Test transpose behavior for out-of-range notes."""

    def test_transpose_below_into_range(self):
        """C1 (MIDI 24) should transpose up to C3."""
        assert midi_note_to_key(24, transpose=True) == ","

    def test_transpose_above_into_range(self):
        """C7 (MIDI 96) should transpose down to C6."""
        assert midi_note_to_key(96, transpose=True) == "i"

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not be affected by transpose."""
        assert midi_note_to_key(60, transpose=False) == "z"

    def test_transpose_defaults_to_false(self):
        """Default behavior should be transpose=False."""
        assert midi_note_to_key(96) is None


class TestOutOfRange:
    """Test out-of-range notes return None when transpose=False."""

    def test_note_below_range(self):
        """MIDI 24 (C1) is below range, should return None."""
        assert midi_note_to_key(24) is None

    def test_note_above_range(self):
        """MIDI 96 (C7) is above range, should return None."""
        assert midi_note_to_key(96) is None
