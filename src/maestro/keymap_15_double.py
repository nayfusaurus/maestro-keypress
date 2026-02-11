"""Heartopia 15-key double row piano key mapping.

Maps MIDI note numbers to keyboard keys for Heartopia's 15-key double row piano.
Two rows of naturals only (no sharps). MIDI note 60 = Middle C = mid row DO.

The piano has 2 rows plus 1 extra note:
- Mid row: A to J (C4-B4, MIDI 60-71, naturals only)
- High row: Q to U (C5-B5, MIDI 72-83, naturals only)
- Extended high: I (C6, MIDI 84)
"""

# Note offsets within an octave (0-11)
# 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B

# Natural note offsets (white keys)
NATURAL_OFFSETS = {0, 2, 4, 5, 7, 9, 11}

# Sharp note offsets (black keys)
SHARP_OFFSETS = {1, 3, 6, 8, 10}

# Map from note offset to key for each row (naturals only)

# High row (C5-B5, MIDI 72-83)
ROW_HIGH = {
    0: "q",  # C (Do)
    2: "w",  # D (Re)
    4: "e",  # E (Mi)
    5: "r",  # F (Fa)
    7: "t",  # G (Sol)
    9: "y",  # A (La)
    11: "u",  # B (Si)
}

# Mid row (C4-B4, MIDI 60-71) - Middle C is here
ROW_MID = {
    0: "a",  # C (Do)
    2: "s",  # D (Re)
    4: "d",  # E (Mi)
    5: "f",  # F (Fa)
    7: "g",  # G (Sol)
    9: "h",  # A (La)
    11: "j",  # B (Si)
}

# Extended high note
EXTENDED_HIGH = "i"  # C6 (MIDI 84)

# MIDI note ranges
MIDI_MID_START = 60  # C4 (Middle C)
MIDI_HIGH_START = 72  # C5
MIDI_HIGH_END = 83  # B5
MIDI_EXTENDED_HIGH = 84  # C6 (highest playable note)

# Sharp-to-nearest-natural mapping for "snap" mode
# Maps sharp note offset to the nearest natural note offset (snaps down)
SHARP_TO_NATURAL = {
    1: 0,  # C# -> C
    3: 2,  # D# -> D
    6: 5,  # F# -> F
    8: 7,  # G# -> G
    10: 9,  # A# -> A
}


def midi_note_to_key_15_double(
    midi_note: int, transpose: bool = False, sharp_handling: str = "skip"
) -> str | None:
    """Convert a MIDI note number to a Heartopia 15-key double row keyboard key.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.
        sharp_handling: How to handle sharp notes:
                        "skip" (default) - return None for sharp notes
                        "snap" - snap to nearest natural note

    Returns:
        Keyboard key character to press, or None if out of range/sharp and skipped
    """
    # Check if note is out of range
    if midi_note < MIDI_MID_START or midi_note > MIDI_EXTENDED_HIGH:
        if not transpose:
            return None
        # Transpose notes into our playable range (60-84)
        while midi_note < MIDI_MID_START:
            midi_note += 12
        while midi_note > MIDI_EXTENDED_HIGH:
            midi_note -= 12

    # Handle extended high note
    if midi_note == MIDI_EXTENDED_HIGH:
        return EXTENDED_HIGH

    # Determine note offset within octave (0-11)
    note_in_octave = midi_note % 12

    # Handle sharp notes
    if note_in_octave in SHARP_OFFSETS:
        if sharp_handling == "snap":
            note_in_octave = SHARP_TO_NATURAL[note_in_octave]
        else:
            # Default "skip" mode - return None for sharps
            return None

    # Determine which row and get the key
    if midi_note >= MIDI_HIGH_START:
        return ROW_HIGH[note_in_octave]
    else:
        return ROW_MID[note_in_octave]
