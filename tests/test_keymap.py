"""Tests for Heartopia 22-key keymap (C3-C6)."""

import pytest

from maestro.keymap import midi_note_to_key


class TestNoteMappings:
    """Smoke-check mappings and boundaries."""

    @pytest.mark.parametrize("note,key", [(48, ","), (60, "z"), (72, "q")])
    def test_one_note_per_octave(self, note, key):
        assert midi_note_to_key(note) == key

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key(47) is None
        assert midi_note_to_key(85) is None


class TestTranspose:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        assert midi_note_to_key(24, transpose=True) == ","

    def test_transpose_above_into_range(self):
        assert midi_note_to_key(96, transpose=True) == "i"

    def test_transpose_does_not_affect_in_range(self):
        assert midi_note_to_key(60, transpose=False) == "z"

    def test_transpose_defaults_to_false(self):
        assert midi_note_to_key(96) is None
