"""Once Human piano key mapping.

Maps MIDI note numbers to keyboard keys for Once Human's 3-octave piano.
Once Human uses a single-octave keyboard layout with modifier-based octave switching.

Base octave (no modifier): MIDI 60-71 (C4-B4)
- White keys: Q=C, W=D, E=E, R=F, T=G, Y=A, U=B
- Black keys: 2=C#, 3=D#, 5=F#, 6=G#, 7=A#

Octave switching:
- Shift (Raise Pitch): MIDI 72-83 (C5-B5) — Shift + same keys
- Ctrl (Lower Pitch): MIDI 48-59 (C3-B3) — Ctrl + same keys
"""

from pynput.keyboard import Key

# Semitone offset (0-11) → keyboard key character
# All 12 chromatic notes are directly accessible per octave
NOTE_TO_KEY: dict[int, str] = {
    0: "q",  # C
    1: "2",  # C#
    2: "w",  # D
    3: "3",  # D#/Eb
    4: "e",  # E
    5: "r",  # F
    6: "5",  # F#
    7: "t",  # G
    8: "6",  # G#/Ab
    9: "y",  # A
    10: "7",  # A#/Bb
    11: "u",  # B
}

# Octave number → modifier key (or None for base octave)
OCTAVE_MODIFIER: dict[int, Key | None] = {
    3: Key.ctrl_l,  # Low octave (MIDI 48-59)
    4: None,  # Base octave (MIDI 60-71)
    5: Key.shift,  # High octave (MIDI 72-83)
}

# MIDI note range
MIN_NOTE = 48  # C3
MAX_NOTE = 83  # B5


def _transpose_to_range(midi_note: int) -> int:
    """Transpose a MIDI note into the playable range (48-83)."""
    while midi_note < MIN_NOTE:
        midi_note += 12
    while midi_note > MAX_NOTE:
        midi_note -= 12
    return midi_note


def midi_note_to_key_once_human(
    midi_note: int, *, transpose: bool = False
) -> tuple[str, int, Key | None] | None:
    """Convert MIDI note to Once Human key mapping.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)
        transpose: If True, transpose out-of-range notes into range.
                   If False (default), return None for out-of-range notes.

    Returns:
        Tuple of (key_character, effective_midi_note, modifier) where modifier is
        Key.shift (octave 5), Key.ctrl_l (octave 3), or None (octave 4).
        Returns None if out of range and transpose=False.
    """
    if midi_note < MIN_NOTE or midi_note > MAX_NOTE:
        if not transpose:
            return None
        midi_note = _transpose_to_range(midi_note)

    semitone = midi_note % 12
    octave = (midi_note // 12) - 1  # MIDI convention: note 60 = C4 → 60//12=5, 5-1=4

    key = NOTE_TO_KEY[semitone]
    modifier = OCTAVE_MODIFIER[octave]

    return (key, midi_note, modifier)
