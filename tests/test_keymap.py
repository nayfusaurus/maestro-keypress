from maestro.keymap import (
    midi_note_to_key,
    OCTAVE_HIGH, OCTAVE_MID, OCTAVE_LOW,
    EXTENDED_HIGH,
)


def test_midi_note_to_key_middle_c():
    """Middle C (MIDI 60) should map to mid octave DO (Z key)."""
    key = midi_note_to_key(60)
    assert key == "z"


def test_midi_note_to_key_c_sharp():
    """C# (MIDI 61) should map to mid octave black key (S key)."""
    key = midi_note_to_key(61)
    assert key == "s"


def test_midi_note_to_key_high_octave():
    """Notes in high range map to high octave keys."""
    key = midi_note_to_key(72)  # C5
    assert key == "q"


def test_midi_note_to_key_low_octave():
    """Notes in low range map to low octave keys."""
    key = midi_note_to_key(48)  # C3
    assert key == ","


def test_midi_note_to_key_extended_high():
    """C6 (MIDI 84) maps to extended high note (I key)."""
    key = midi_note_to_key(84)
    assert key == "i"


def test_midi_note_to_key_transpose_too_high():
    """Notes above range get transposed down when transpose=True."""
    key = midi_note_to_key(96, transpose=True)  # C7 - way too high, transposes to C6
    assert key == "i"  # Extended high note


def test_midi_note_to_key_transpose_too_low():
    """Notes below range get transposed up when transpose=True."""
    key = midi_note_to_key(24, transpose=True)  # C1 - way too low, transposes to C3
    assert key == ","  # Low octave DO


def test_octave_mappings_complete():
    """Each octave has 12 keys (7 white + 5 black)."""
    assert len(OCTAVE_HIGH) == 12
    assert len(OCTAVE_MID) == 12
    assert len(OCTAVE_LOW) == 12


def test_low_octave_black_keys():
    """Verify low octave black keys are correctly mapped."""
    assert midi_note_to_key(54) == "0"  # F#3
    assert midi_note_to_key(56) == "-"  # G#3


class TestTransposeParameter:
    """Tests for the transpose parameter."""

    def test_transpose_true_transposes_high_note(self):
        """With transpose=True, notes above range get transposed down."""
        key = midi_note_to_key(96, transpose=True)  # C7
        assert key == "i"  # Transposed to C6

    def test_transpose_true_transposes_low_note(self):
        """With transpose=True, notes below range get transposed up."""
        key = midi_note_to_key(24, transpose=True)  # C1
        assert key == ","  # Transposed to C3

    def test_transpose_false_returns_none_for_high_note(self):
        """With transpose=False, notes above range return None."""
        key = midi_note_to_key(96, transpose=False)  # C7
        assert key is None

    def test_transpose_false_returns_none_for_low_note(self):
        """With transpose=False, notes below range return None."""
        key = midi_note_to_key(24, transpose=False)  # C1
        assert key is None

    def test_transpose_false_returns_key_for_in_range_note(self):
        """With transpose=False, notes in range still return keys."""
        key = midi_note_to_key(60, transpose=False)  # Middle C
        assert key == "z"

    def test_transpose_defaults_to_false(self):
        """Default behavior should be transpose=False (returns None for out-of-range)."""
        # This test documents the NEW default behavior
        key = midi_note_to_key(96)  # C7, no transpose param
        assert key is None
