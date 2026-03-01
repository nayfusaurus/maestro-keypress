"""Tests for Heartopia 15-key double row keymap."""

import pytest
from maestro.keymap_15_double import midi_note_to_key_15_double


class TestNoteMappings:
    """Smoke-check mappings and boundaries."""

    @pytest.mark.parametrize("note,key", [(60, "a"), (72, "q"), (84, "i")])
    def test_one_note_per_row(self, note, key):
        assert midi_note_to_key_15_double(note) == key

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key_15_double(59) is None
        assert midi_note_to_key_15_double(85) is None


class TestSharpHandling:
    """Test skip and snap modes for sharp notes."""

    @pytest.mark.parametrize("note", [61, 66])
    def test_sharp_skip_returns_none(self, note):
        assert midi_note_to_key_15_double(note) is None

    @pytest.mark.parametrize("note,key", [(61, "a"), (66, "f")])
    def test_sharp_snap_returns_natural(self, note, key):
        assert midi_note_to_key_15_double(note, sharp_handling="snap") == key


class TestTranspose:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        assert midi_note_to_key_15_double(48, transpose=True) == "a"

    def test_transpose_above_into_range(self):
        assert midi_note_to_key_15_double(96, transpose=True) == "i"

    def test_transpose_does_not_affect_in_range(self):
        assert midi_note_to_key_15_double(60, transpose=True) == "a"

    def test_transpose_sharp_with_snap_mode(self):
        assert midi_note_to_key_15_double(49, transpose=True, sharp_handling="snap") == "a"
