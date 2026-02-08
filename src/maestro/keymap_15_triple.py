"""Heartopia 15-key triple row piano mapping.

Maps MIDI note numbers to keyboard keys for Heartopia's 15-key piano.
Three rows of 5 keys, naturals only (no sharps). Range: MIDI 60-84 (C4 to C6).
Notes flow continuously across rows.

- Row 1: Y, U, I, O, P  (C4-G4, MIDI 60-67)
- Row 2: H, J, K, L, ;  (A4-E5, MIDI 69-76)
- Row 3: N, M, ,, ., /  (F5-C6, MIDI 77-84)
"""

# Direct MIDI note to key mapping (naturals only)
NOTE_MAP = {
    60: "y",   # C4 (Row 1)
    62: "u",   # D4 (Row 1)
    64: "i",   # E4 (Row 1)
    65: "o",   # F4 (Row 1)
    67: "p",   # G4 (Row 1)
    69: "h",   # A4 (Row 2)
    71: "j",   # B4 (Row 2)
    72: "k",   # C5 (Row 2)
    74: "l",   # D5 (Row 2)
    76: ";",   # E5 (Row 2)
    77: "n",   # F5 (Row 3)
    79: "m",   # G5 (Row 3)
    81: ",",   # A5 (Row 3)
    83: ".",   # B5 (Row 3)
    84: "/",   # C6 (Row 3)
}

# MIDI note range
MIDI_LOW = 60   # C4
MIDI_HIGH = 84  # C6

# Note offsets within an octave (0-11)
NATURAL_OFFSETS = {0, 2, 4, 5, 7, 9, 11}
SHARP_OFFSETS = {1, 3, 6, 8, 10}

# Sharp note mappings: sharp offset -> nearest natural offset
# C#(1)->C(0), D#(3)->D(2), F#(6)->F(5), G#(8)->G(7), A#(10)->A(9)
SHARP_TO_NATURAL = {
    1: 0,   # C# -> C
    3: 2,   # D# -> D
    6: 5,   # F# -> F
    8: 7,   # G# -> G
    10: 9,  # A# -> A
}


def midi_note_to_key_15_triple(midi_note: int, transpose: bool = False, sharp_handling: str = "skip") -> str | None:
    """Convert a MIDI note number to a Heartopia 15-key triple row keyboard key.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.
        sharp_handling: How to handle sharp notes:
                        "skip" (default) - return None for sharp notes
                        "snap" - snap to nearest natural note

    Returns:
        Keyboard key character to press, or None if unmappable
    """
    # Check if note is out of range
    if midi_note < MIDI_LOW or midi_note > MIDI_HIGH:
        if not transpose:
            return None
        # Transpose notes into our playable range (60-84)
        while midi_note < MIDI_LOW:
            midi_note += 12
        while midi_note > MIDI_HIGH:
            midi_note -= 12

    # Determine note offset within octave (0-11)
    note_in_octave = midi_note % 12

    # Check if this is a sharp note
    if note_in_octave in SHARP_OFFSETS:
        if sharp_handling == "skip":
            return None
        elif sharp_handling == "snap":
            # Snap to nearest natural note
            natural_offset = SHARP_TO_NATURAL[note_in_octave]
            midi_note = midi_note - note_in_octave + natural_offset

    # Look up in NOTE_MAP
    return NOTE_MAP.get(midi_note)
