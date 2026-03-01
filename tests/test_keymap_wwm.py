"""Tests for Where Winds Meet (WWM) keymap."""

import pytest
from pynput.keyboard import Key

from maestro.keymap_wwm import midi_note_to_key_wwm


class TestNoteMappings:
    """Smoke-check naturals, sharps, and boundaries."""

    @pytest.mark.parametrize(
        "note,expected",
        [
            (48, ("z", None)),  # C3 natural
            (60, ("a", None)),  # C4 natural
            (72, ("q", None)),  # C5 natural
            (49, ("z", Key.shift)),  # C#3 sharp
            (61, ("a", Key.shift)),  # C#4 sharp
        ],
    )
    def test_naturals_and_sharps(self, note, expected):
        assert midi_note_to_key_wwm(note) == expected

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key_wwm(47) is None
        assert midi_note_to_key_wwm(84) is None


class TestTranspose:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        assert midi_note_to_key_wwm(36, transpose=True) == ("z", None)

    def test_transpose_above_into_range(self):
        assert midi_note_to_key_wwm(84, transpose=True) == ("q", None)

    def test_transpose_does_not_affect_in_range(self):
        assert midi_note_to_key_wwm(60, transpose=True) == ("a", None)

    def test_transpose_preserves_sharp_modifier(self):
        assert midi_note_to_key_wwm(37, transpose=True) == ("z", Key.shift)
