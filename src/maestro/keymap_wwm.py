"""Where Winds Meet (WWM) piano key mapping.

Maps MIDI note numbers to keyboard keys for WWM's 3-octave piano.
WWM uses numbered notation (1-7 = Do-Re-Mi-Fa-Sol-La-Si) with Shift modifier for sharps.

The piano has 3 octaves:
- Low octave: C3-B3 (MIDI 48-59) → Z, X, C, V, B, N, M
- Medium octave: C4-B4 (MIDI 60-71) → A, S, D, F, G, H, J
- High octave: C5-B5 (MIDI 72-83) → Q, W, E, R, T, Y, U

Sharp notes use Shift modifier on the natural note's key.
"""

from pynput.keyboard import Key

# Note offsets within an octave (0-11)
# 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B

# Map from note offset to (key, is_sharp)
# Natural notes: C(0), D(2), E(4), F(5), G(7), A(9), B(11)
# Sharp notes: C#(1), D#(3), F#(6), G#(8), A#(10)

# High octave keys (C5-B5, MIDI 72-83): Q, W, E, R, T, Y, U
OCTAVE_HIGH_KEYS = {
    0: "q",   # C (Do)
    2: "w",   # D (Re)
    4: "e",   # E (Mi)
    5: "r",   # F (Fa)
    7: "t",   # G (Sol)
    9: "y",   # A (La)
    11: "u",  # B (Si)
}

# Medium octave keys (C4-B4, MIDI 60-71): A, S, D, F, G, H, J
OCTAVE_MID_KEYS = {
    0: "a",   # C (Do)
    2: "s",   # D (Re)
    4: "d",   # E (Mi)
    5: "f",   # F (Fa)
    7: "g",   # G (Sol)
    9: "h",   # A (La)
    11: "j",  # B (Si)
}

# Low octave keys (C3-B3, MIDI 48-59): Z, X, C, V, B, N, M
OCTAVE_LOW_KEYS = {
    0: "z",   # C (Do)
    2: "x",   # D (Re)
    4: "c",   # E (Mi)
    5: "v",   # F (Fa)
    7: "b",   # G (Sol)
    9: "n",   # A (La)
    11: "m",  # B (Si)
}

# Sharp note mappings: sharp offset -> natural offset
# C#(1)->C(0), D#(3)->D(2), F#(6)->F(5), G#(8)->G(7), A#(10)->A(9)
SHARP_TO_NATURAL = {
    1: 0,   # C# -> C
    3: 2,   # D# -> D
    6: 5,   # F# -> F
    8: 7,   # G# -> G
    10: 9,  # A# -> A
}

# MIDI note ranges for WWM (3 octaves, no extended notes)
MIDI_LOW_START = 48   # C3
MIDI_MID_START = 60   # C4 (Middle C)
MIDI_HIGH_START = 72  # C5
MIDI_HIGH_END = 83    # B5


def midi_note_to_key_wwm(midi_note: int, transpose: bool = False) -> tuple[str, Key | None] | None:
    """Convert MIDI note to WWM key + optional Shift modifier.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.

    Returns:
        Tuple of (key_character, modifier) where modifier is Key.shift or None,
        or None if out of range and transpose=False
    """
    # Check if note is out of range
    if midi_note < MIDI_LOW_START or midi_note > MIDI_HIGH_END:
        if not transpose:
            return None
        # Transpose notes into our playable range (48-83)
        while midi_note < MIDI_LOW_START:
            midi_note += 12
        while midi_note > MIDI_HIGH_END:
            midi_note -= 12

    # Determine note offset within octave (0-11)
    note_in_octave = midi_note % 12

    # Check if this is a sharp note
    is_sharp = note_in_octave in SHARP_TO_NATURAL
    if is_sharp:
        # Use the natural note's key with Shift modifier
        natural_offset = SHARP_TO_NATURAL[note_in_octave]
    else:
        natural_offset = note_in_octave

    # Determine which octave and get the key
    if midi_note >= MIDI_HIGH_START:
        key = OCTAVE_HIGH_KEYS[natural_offset]
    elif midi_note >= MIDI_MID_START:
        key = OCTAVE_MID_KEYS[natural_offset]
    else:
        key = OCTAVE_LOW_KEYS[natural_offset]

    modifier = Key.shift if is_sharp else None
    return (key, modifier)
