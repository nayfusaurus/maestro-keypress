"""Heartopia piano key mapping.

Maps MIDI note numbers to keyboard keys for Heartopia's 3-octave piano.
MIDI note 60 = Middle C = mid octave DO.

The piano has 3 full octaves plus 2 extra notes:
- Lowest: , (C2, MIDI 36)
- Low octave: L to ] (C3-B3, MIDI 48-59)
- Mid octave: Z to M (C4-B4, MIDI 60-71)
- High octave: Q to U (C5-B5, MIDI 72-83)
- Highest: I (C6, MIDI 84)
"""

# Note offsets within an octave (0-11)
# 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F, 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B

# High octave (C5-B5, MIDI 72-83)
OCTAVE_HIGH = {
    0: "q",   # DO (C)
    1: "2",   # DO# (C#)
    2: "w",   # RE (D)
    3: "3",   # RE# (D#)
    4: "e",   # MI (E)
    5: "r",   # FA (F)
    6: "5",   # FA# (F#)
    7: "t",   # SOL (G)
    8: "6",   # SOL# (G#)
    9: "y",   # LA (A)
    10: "7",  # LA# (A#)
    11: "u",  # SI (B)
}

# Mid octave (C4-B4, MIDI 60-71) - Middle C is here
OCTAVE_MID = {
    0: "z",   # DO (C)
    1: "s",   # DO# (C#)
    2: "x",   # RE (D)
    3: "d",   # RE# (D#)
    4: "c",   # MI (E)
    5: "v",   # FA (F)
    6: "g",   # FA# (F#)
    7: "b",   # SOL (G)
    8: "h",   # SOL# (G#)
    9: "n",   # LA (A)
    10: "j",  # LA# (A#)
    11: "m",  # SI (B)
}

# Low octave (C3-B3, MIDI 48-59)
OCTAVE_LOW = {
    0: "l",   # DO (C)
    1: ".",   # DO# (C#)
    2: ";",   # RE (D)
    3: "'",   # RE# (D#)
    4: "/",   # MI (E)
    5: "o",   # FA (F)
    6: "0",   # FA# (F#) - between O and P
    7: "p",   # SOL (G)
    8: "-",   # SOL# (G#) - between P and [
    9: "[",   # LA (A)
    10: "=",  # LA# (A#)
    11: "]",  # SI (B)
}

# Extended notes beyond the 3 main octaves
EXTENDED_LOW = ","   # C2 (MIDI 36) - lowest DO with bottom dot
EXTENDED_HIGH = "i"  # C6 (MIDI 84) - highest DO with 2 dots

# MIDI note ranges
MIDI_EXTENDED_LOW = 36   # C2 (lowest playable note)
MIDI_LOW_START = 48      # C3
MIDI_MID_START = 60      # C4 (Middle C)
MIDI_HIGH_START = 72     # C5
MIDI_HIGH_END = 83       # B5
MIDI_EXTENDED_HIGH = 84  # C6 (highest playable note)


def midi_note_to_key(midi_note: int) -> str:
    """Convert a MIDI note number to a Heartopia keyboard key.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)

    Returns:
        Keyboard key character to press
    """
    # Transpose notes into our playable range (36-84)
    while midi_note < MIDI_EXTENDED_LOW:
        midi_note += 12
    while midi_note > MIDI_EXTENDED_HIGH:
        midi_note -= 12

    # Handle extended notes
    if midi_note == MIDI_EXTENDED_LOW:
        return EXTENDED_LOW
    if midi_note == MIDI_EXTENDED_HIGH:
        return EXTENDED_HIGH

    # Determine which octave and note offset
    note_in_octave = midi_note % 12

    if midi_note >= MIDI_HIGH_START:
        return OCTAVE_HIGH[note_in_octave]
    elif midi_note >= MIDI_MID_START:
        return OCTAVE_MID[note_in_octave]
    else:
        return OCTAVE_LOW[note_in_octave]
