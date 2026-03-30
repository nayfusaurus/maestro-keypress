"""Tests for Once Human keymap."""

import pytest
from pynput.keyboard import Key

from maestro.keymap_once_human import midi_note_to_key_once_human


class TestNoteMapping:
    """Test MIDI note to key mapping across all 3 octaves."""

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (60, "q"),  # C4
            (62, "w"),  # D4
            (64, "e"),  # E4
            (65, "r"),  # F4
            (67, "t"),  # G4
            (69, "y"),  # A4
            (71, "u"),  # B4
        ],
    )
    def test_base_octave_naturals(self, note, expected_key):
        """Base octave (MIDI 60-71) should use no modifier."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, None)

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (61, "2"),  # C#4
            (63, "3"),  # D#4
            (66, "5"),  # F#4
            (68, "6"),  # G#4
            (70, "7"),  # A#4
        ],
    )
    def test_base_octave_accidentals(self, note, expected_key):
        """Accidentals in base octave should use number keys, no modifier."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, None)

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (72, "q"),  # C5
            (74, "w"),  # D5
            (76, "e"),  # E5
            (77, "r"),  # F5
            (79, "t"),  # G5
            (81, "y"),  # A5
            (83, "u"),  # B5
        ],
    )
    def test_high_octave_naturals(self, note, expected_key):
        """High octave (MIDI 72-83) should use Shift modifier."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, Key.shift)

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (73, "2"),  # C#5
            (75, "3"),  # D#5
            (78, "5"),  # F#5
            (80, "6"),  # G#5
            (82, "7"),  # A#5
        ],
    )
    def test_high_octave_accidentals(self, note, expected_key):
        """Accidentals in high octave should use Shift + number key."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, Key.shift)

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (48, "q"),  # C3
            (50, "w"),  # D3
            (52, "e"),  # E3
            (53, "r"),  # F3
            (55, "t"),  # G3
            (57, "y"),  # A3
            (59, "u"),  # B3
        ],
    )
    def test_low_octave_naturals(self, note, expected_key):
        """Low octave (MIDI 48-59) should use Ctrl modifier."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, Key.ctrl_l)

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (49, "2"),  # C#3
            (51, "3"),  # D#3
            (54, "5"),  # F#3
            (56, "6"),  # G#3
            (58, "7"),  # A#3
        ],
    )
    def test_low_octave_accidentals(self, note, expected_key):
        """Accidentals in low octave should use Ctrl + number key."""
        assert midi_note_to_key_once_human(note) == (expected_key, note, Key.ctrl_l)


class TestOutOfRange:
    """Test out-of-range notes."""

    def test_below_range_returns_none(self):
        assert midi_note_to_key_once_human(47) is None

    def test_above_range_returns_none(self):
        assert midi_note_to_key_once_human(84) is None

    def test_very_low_returns_none(self):
        assert midi_note_to_key_once_human(0) is None

    def test_very_high_returns_none(self):
        assert midi_note_to_key_once_human(127) is None


class TestTranspose:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        """MIDI 36 (C2) should transpose up to C3."""
        assert midi_note_to_key_once_human(36, transpose=True) == ("q", 48, Key.ctrl_l)

    def test_transpose_above_into_range(self):
        """MIDI 84 (C6) should transpose down to C5."""
        assert midi_note_to_key_once_human(84, transpose=True) == ("q", 72, Key.shift)

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not change when transpose=True."""
        assert midi_note_to_key_once_human(60, transpose=True) == ("q", 60, None)

    def test_transpose_preserves_accidental(self):
        """MIDI 37 (C#2) should transpose to C#3 with Ctrl."""
        assert midi_note_to_key_once_human(37, transpose=True) == ("2", 49, Key.ctrl_l)

    def test_transpose_very_low(self):
        """MIDI 12 (C0) should transpose up into range."""
        assert midi_note_to_key_once_human(12, transpose=True) == ("q", 48, Key.ctrl_l)

    def test_transpose_very_high(self):
        """MIDI 96 (C7) should transpose down into range."""
        assert midi_note_to_key_once_human(96, transpose=True) == ("q", 72, Key.shift)
