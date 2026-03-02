"""Where Winds Meet (WWM) piano key mapping.

Maps MIDI note numbers to keyboard keys for WWM's 3-octave piano.
WWM uses numbered notation (1-7 = Do-Re-Mi-Fa-Sol-La-Si).

36-key layout: All 12 chromatic notes per octave using two modifiers:
- Shift ("higher semitone"): C#, F#, G# — Shift + the natural key below
- Ctrl ("lower semitone"): Eb, Bb — Ctrl + the natural key above

21-key layout: 7 natural notes per octave, no modifiers.

The piano has 3 octaves:
- Low octave: C3-B3 (MIDI 48-59) → Z, X, C, V, B, N, M
- Medium octave: C4-B4 (MIDI 60-71) → A, S, D, F, G, H, J
- High octave: C5-B5 (MIDI 72-83) → Q, W, E, R, T, Y, U
"""

from pynput.keyboard import Key

# Note offsets within an octave (0-11)
# 0=C, 1=C#, 2=D, 3=Eb, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=Bb, 11=B

# Natural notes: C(0), D(2), E(4), F(5), G(7), A(9), B(11)

# High octave keys (C5-B5, MIDI 72-83): Q, W, E, R, T, Y, U
OCTAVE_HIGH_KEYS = {
    0: "q",  # C (Do)
    2: "w",  # D (Re)
    4: "e",  # E (Mi)
    5: "r",  # F (Fa)
    7: "t",  # G (Sol)
    9: "y",  # A (La)
    11: "u",  # B (Si)
}

# Medium octave keys (C4-B4, MIDI 60-71): A, S, D, F, G, H, J
OCTAVE_MID_KEYS = {
    0: "a",  # C (Do)
    2: "s",  # D (Re)
    4: "d",  # E (Mi)
    5: "f",  # F (Fa)
    7: "g",  # G (Sol)
    9: "h",  # A (La)
    11: "j",  # B (Si)
}

# Low octave keys (C3-B3, MIDI 48-59): Z, X, C, V, B, N, M
OCTAVE_LOW_KEYS = {
    0: "z",  # C (Do)
    2: "x",  # D (Re)
    4: "c",  # E (Mi)
    5: "v",  # F (Fa)
    7: "b",  # G (Sol)
    9: "n",  # A (La)
    11: "m",  # B (Si)
}

# 36-key accidental mappings (two modifier groups):

# Shift accidentals ("higher semitone"): accidental offset → natural key offset
# Press Shift + the natural key below to raise it by a semitone
SHIFT_ACCIDENTALS = {
    1: 0,  # C# → Shift + C key
    6: 5,  # F# → Shift + F key
    8: 7,  # G# → Shift + G key
}

# Ctrl accidentals ("lower semitone"): accidental offset → natural key offset
# Press Ctrl + the natural key above to lower it by a semitone
CTRL_ACCIDENTALS = {
    3: 4,  # Eb → Ctrl + E key
    10: 11,  # Bb → Ctrl + B key
}

# Combined sharp-to-natural mapping for 21-key snap logic
# Maps each accidental to the nearest lower natural note
SHARP_TO_NATURAL = {
    1: 0,  # C# → C
    3: 2,  # Eb → D
    6: 5,  # F# → F
    8: 7,  # G# → G
    10: 9,  # Bb → A
}

# MIDI note ranges for WWM (3 octaves, no extended notes)
MIDI_LOW_START = 48  # C3
MIDI_MID_START = 60  # C4 (Middle C)
MIDI_HIGH_START = 72  # C5
MIDI_HIGH_END = 83  # B5


def _get_octave_key(midi_note: int, natural_offset: int) -> str:
    """Look up the key character for a natural note offset in the correct octave."""
    if midi_note >= MIDI_HIGH_START:
        return OCTAVE_HIGH_KEYS[natural_offset]
    elif midi_note >= MIDI_MID_START:
        return OCTAVE_MID_KEYS[natural_offset]
    else:
        return OCTAVE_LOW_KEYS[natural_offset]


def _transpose_to_range(midi_note: int) -> int:
    """Transpose a MIDI note into the playable range (48-83)."""
    while midi_note < MIDI_LOW_START:
        midi_note += 12
    while midi_note > MIDI_HIGH_END:
        midi_note -= 12
    return midi_note


def midi_note_to_key_wwm(midi_note: int, transpose: bool = False) -> tuple[str, Key | None] | None:
    """Convert MIDI note to WWM 36-key layout: key + Shift/Ctrl modifier.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.

    Returns:
        Tuple of (key_character, modifier) where modifier is Key.shift,
        Key.ctrl_l, or None. Returns None if out of range and transpose=False.
    """
    if midi_note < MIDI_LOW_START or midi_note > MIDI_HIGH_END:
        if not transpose:
            return None
        midi_note = _transpose_to_range(midi_note)

    note_in_octave = midi_note % 12

    # Shift accidentals: C#, F#, G#
    if note_in_octave in SHIFT_ACCIDENTALS:
        natural_offset = SHIFT_ACCIDENTALS[note_in_octave]
        key = _get_octave_key(midi_note, natural_offset)
        return (key, Key.shift)

    # Ctrl accidentals: Eb, Bb
    if note_in_octave in CTRL_ACCIDENTALS:
        natural_offset = CTRL_ACCIDENTALS[note_in_octave]
        key = _get_octave_key(midi_note, natural_offset)
        return (key, Key.ctrl_l)

    # Natural note
    key = _get_octave_key(midi_note, note_in_octave)
    return (key, None)


def midi_note_to_key_wwm_21(
    midi_note: int, transpose: bool = False, sharp_handling: str = "skip"
) -> tuple[str, None] | None:
    """Convert MIDI note to WWM 21-key layout: naturals only, no modifiers.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.
        sharp_handling: "skip" to return None for accidentals,
                        "snap" to map to nearest lower natural.

    Returns:
        Tuple of (key_character, None) or None if note cannot be played.
    """
    if midi_note < MIDI_LOW_START or midi_note > MIDI_HIGH_END:
        if not transpose:
            return None
        midi_note = _transpose_to_range(midi_note)

    note_in_octave = midi_note % 12

    # Check if this is an accidental
    if note_in_octave in SHARP_TO_NATURAL:
        if sharp_handling == "snap":
            natural_offset = SHARP_TO_NATURAL[note_in_octave]
            key = _get_octave_key(midi_note, natural_offset)
            return (key, None)
        return None  # skip

    # Natural note
    key = _get_octave_key(midi_note, note_in_octave)
    return (key, None)
