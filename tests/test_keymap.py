"""Tests for Heartopia 22-key keymap (C3-C6)."""

import pytest

from maestro.keymap import midi_note_to_key


class TestNoteMappings:
    """Smoke-check mappings and boundaries."""

    @pytest.mark.parametrize("note,expected", [(48, (",", 48)), (60, ("z", 60)), (72, ("q", 72))])
    def test_one_note_per_octave(self, note, expected):
        assert midi_note_to_key(note) == expected

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key(47) is None
        assert midi_note_to_key(85) is None


class TestTranspose:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        # 24 transposes up 2 octaves to 48
        assert midi_note_to_key(24, transpose=True) == (",", 48)

    def test_transpose_above_into_range(self):
        # 96 transposes down 1 octave to 84
        assert midi_note_to_key(96, transpose=True) == ("i", 84)

    def test_transpose_does_not_affect_in_range(self):
        assert midi_note_to_key(60, transpose=False) == ("z", 60)

    def test_transpose_defaults_to_false(self):
        assert midi_note_to_key(96) is None
