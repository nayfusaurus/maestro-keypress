from maestro.keymap import (
    midi_note_to_key,
    OCTAVE_HIGH, OCTAVE_MID, OCTAVE_LOW,
    EXTENDED_HIGH, EXTENDED_LOW,
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
    assert key == "l"


def test_midi_note_to_key_extended_high():
    """C6 (MIDI 84) maps to extended high note (I key)."""
    key = midi_note_to_key(84)
    assert key == "i"


def test_midi_note_to_key_extended_low():
    """C2 (MIDI 36) maps to extended low note (, key)."""
    key = midi_note_to_key(36)
    assert key == ","


def test_midi_note_to_key_transpose_too_high():
    """Notes above range get transposed down."""
    key = midi_note_to_key(96)  # C7 - way too high, transposes to C6
    assert key == "i"  # Extended high note


def test_midi_note_to_key_transpose_too_low():
    """Notes below range get transposed up."""
    key = midi_note_to_key(24)  # C1 - way too low, transposes to C2
    assert key == ","  # Extended low note


def test_octave_mappings_complete():
    """Each octave has 12 keys (7 white + 5 black)."""
    assert len(OCTAVE_HIGH) == 12
    assert len(OCTAVE_MID) == 12
    assert len(OCTAVE_LOW) == 12


def test_low_octave_black_keys():
    """Verify low octave black keys are correctly mapped."""
    assert midi_note_to_key(54) == "0"  # F#3
    assert midi_note_to_key(56) == "-"  # G#3
