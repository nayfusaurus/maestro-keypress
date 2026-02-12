"""Tests for Heartopia 8-key xylophone keymap."""

import pytest
from maestro.keymap_xylophone import midi_note_to_key, MIN_NOTE, MAX_NOTE


class TestXylophoneMappings:
    """Test all 8 xylophone notes map correctly (natural notes only)."""

    @pytest.mark.parametrize(
        "note,key",
        [
            (60, "a"),  # C4 - DO
            (62, "s"),  # D4 - RE
            (64, "d"),  # E4 - MI
            (65, "f"),  # F4 - FA
            (67, "g"),  # G4 - SOL
            (69, "h"),  # A4 - LA
            (71, "j"),  # B4 - SI
            (72, "k"),  # C5 - DO
        ],
    )
    def test_xylophone_note_mappings(self, note, key):
        """All 8 natural notes should map to correct keys (A-K)."""
        assert midi_note_to_key(note) == key


class TestConstants:
    """Test MIN_NOTE and MAX_NOTE constants."""

    def test_min_note_is_60(self):
        """MIN_NOTE should be 60 (C4)."""
        assert MIN_NOTE == 60

    def test_max_note_is_72(self):
        """MAX_NOTE should be 72 (C5)."""
        assert MAX_NOTE == 72


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN_NOTE (60) should be valid."""
        assert midi_note_to_key(MIN_NOTE) == "a"

    def test_max_note_boundary(self):
        """Note at MAX_NOTE (72) should be valid."""
        assert midi_note_to_key(MAX_NOTE) == "k"

    def test_note_below_min_is_invalid(self):
        """Note below MIN_NOTE should return None."""
        assert midi_note_to_key(MIN_NOTE - 1) is None


class TestSharpNotes:
    """Test that sharp/flat notes (non-natural) return None."""

    @pytest.mark.parametrize(
        "note",
        [
            61,  # C#4
            63,  # D#4
            66,  # F#4
            68,  # G#4
            70,  # A#4
        ],
    )
    def test_sharp_notes_return_none(self, note):
        """Sharp notes should return None (only natural notes are mapped)."""
        assert midi_note_to_key(note) is None


class TestTranspose:
    """Test transpose parameter behavior for xylophone."""

    def test_transpose_true_ignored(self):
        """Transpose=True should have no effect on xylophone."""
        assert midi_note_to_key(60, transpose=True) == "a"
        assert midi_note_to_key(72, transpose=True) == "k"

    def test_transpose_false_works_normally(self):
        """Transpose=False should work normally."""
        assert midi_note_to_key(60, transpose=False) == "a"


class TestOutOfRange:
    """Test out-of-range notes return None."""

    def test_note_below_range_immediate(self):
        """MIDI 59 (B3) is immediately below range, should return None."""
        assert midi_note_to_key(59) is None

    def test_note_above_range_immediate(self):
        """MIDI 73 (C#5) is immediately above range, should return None."""
        assert midi_note_to_key(73) is None

    def test_note_far_below_range(self):
        """MIDI 36 (C2) is far below range, should return None."""
        assert midi_note_to_key(36) is None

    def test_note_far_above_range(self):
        """MIDI 96 (C7) is far above range, should return None."""
        assert midi_note_to_key(96) is None
