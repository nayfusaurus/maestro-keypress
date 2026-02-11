"""Tests for Heartopia 8-key drum keymap."""

import pytest
from maestro.keymap_drums import midi_note_to_key, MIN_NOTE, MAX_NOTE


class TestDrumMappings:
    """Test all 8 drum notes map correctly (MIDI 60-67)."""

    @pytest.mark.parametrize(
        "note,key",
        [
            (60, "y"),  # C4
            (61, "u"),  # C#4
            (62, "i"),  # D4
            (63, "o"),  # D#4
            (64, "h"),  # E4
            (65, "j"),  # F4
            (66, "k"),  # F#4
            (67, "l"),  # G4
        ],
    )
    def test_drum_note_mappings(self, note, key):
        """All 8 drum notes should map to correct keys (YUIO/HJKL)."""
        assert midi_note_to_key(note) == key


class TestConstants:
    """Test MIN_NOTE and MAX_NOTE constants."""

    def test_min_note_is_60(self):
        """MIN_NOTE should be 60 (C4)."""
        assert MIN_NOTE == 60

    def test_max_note_is_67(self):
        """MAX_NOTE should be 67 (G4)."""
        assert MAX_NOTE == 67


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN_NOTE (60) should be valid."""
        assert midi_note_to_key(MIN_NOTE) == "y"

    def test_max_note_boundary(self):
        """Note at MAX_NOTE (67) should be valid."""
        assert midi_note_to_key(MAX_NOTE) == "l"

    def test_note_below_min_is_invalid(self):
        """Note below MIN_NOTE should return None."""
        assert midi_note_to_key(MIN_NOTE - 1) is None


class TestTranspose:
    """Test transpose parameter behavior for drums."""

    def test_transpose_true_ignored(self):
        """Transpose=True should have no effect on drums."""
        assert midi_note_to_key(60, transpose=True) == "y"
        assert midi_note_to_key(67, transpose=True) == "l"

    def test_transpose_false_works_normally(self):
        """Transpose=False should work normally."""
        assert midi_note_to_key(60, transpose=False) == "y"


class TestOutOfRange:
    """Test out-of-range notes return None."""

    def test_note_below_range_immediate(self):
        """MIDI 59 (B3) is immediately below range, should return None."""
        assert midi_note_to_key(59) is None

    def test_note_above_range_immediate(self):
        """MIDI 68 (G#4) is immediately above range, should return None."""
        assert midi_note_to_key(68) is None

    def test_note_far_below_range(self):
        """MIDI 36 (C2) is far below range, should return None."""
        assert midi_note_to_key(36) is None

    def test_note_far_above_range(self):
        """MIDI 96 (C7) is far above range, should return None."""
        assert midi_note_to_key(96) is None
