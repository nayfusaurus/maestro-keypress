# Building Maestro: An Auto-Play Piano Bot for Heartopia

Ever wanted to play beautiful piano songs in Heartopia but can't quite nail the timing? I built Maestro - a simple Python app that plays MIDI songs for you by simulating keyboard presses.

## The Problem

Heartopia has an in-game piano with 38 keys (3 octaves plus 2 extra notes). Playing songs manually requires precise timing and knowing which keys to press. MIDI files contain all the note data - we just need to translate them into keypresses.

## The Solution

Maestro reads MIDI files, maps each note to the correct keyboard key, and presses them at the right time. Here's how it works:

```
MIDI File -> Parse Notes -> Map to Keys -> Simulate Keypresses
```

## Tech Stack

- **Python 3.11+** - Simple and readable
- **mido** - Parses MIDI files into note events
- **pynput** - Simulates keyboard presses and listens for hotkeys
- **tkinter** - Built-in GUI library for the song picker

## Key Challenges

### 1. Mapping MIDI Notes to Keys

MIDI uses numbers 0-127 for notes (Middle C = 60). Heartopia's piano only covers MIDI notes 36-84. The solution: transpose notes outside this range up or down by octaves until they fit.

```python
while midi_note < 36:
    midi_note += 12  # Move up an octave
while midi_note > 84:
    midi_note -= 12  # Move down an octave
```

### 2. Timing the Keypresses

MIDI files store timing as "ticks" relative to tempo. We convert these to real seconds, then sleep between notes:

```python
for note in notes:
    wait_time = note.time - current_time
    time.sleep(wait_time)
    keyboard.press(note.key)
```

### 3. Global Hotkeys

Users need to control playback even when Heartopia has focus. pynput's `Listener` captures F1/F2/F3 globally.

### 4. WSL Limitation

pynput needs direct access to input devices, which WSL can't provide. Solution: build a Windows exe with PyInstaller.

## Architecture

```
Maestro (coordinator)
    |
    +-- Player (background thread)
    |       |-- parser.py (MIDI -> notes)
    |       |-- keymap.py (notes -> keys)
    |
    +-- SongPicker (GUI)
```

The player runs in a daemon thread so it doesn't block the GUI. A 3-second delay after selecting a song gives you time to switch to the game.

## The Keymap

Heartopia's piano layout (from the game screenshots):

| Octave | DO  | DO# | RE  | RE# | MI  | FA  | FA# | SOL | SOL# | LA  | LA# | SI  |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|------|-----|-----|-----|
| High   | Q   | 2   | W   | 3   | E   | R   | 5   | T   | 6    | Y   | 7   | U   |
| Mid    | Z   | S   | X   | D   | C   | V   | G   | B   | H    | N   | J   | M   |
| Low    | L   | .   | ;   | '   | /   | O   | 0   | P   | -    | [   | =   | ]   |

Plus extended notes: `,` (lowest) and `I` (highest).

## Result

A simple GUI with:
- Song list with search
- Progress bar showing playback position
- Play/Pause/Stop controls
- Folder browser

Press F1 to open the picker, select a song, switch to Heartopia, and enjoy automatic piano playing!

## Lessons Learned

1. **Start simple** - The first version just played notes. Features like pause, progress tracking, and search came later.
2. **Test the mapping early** - Wrong key mappings are hard to debug. Write tests for the keymap first.
3. **Threading is tricky** - Events and flags help coordinate between the playback thread and GUI.

## Try It Yourself

```bash
git clone <repo-url>
cd maestro-keypress
uv sync
uv run maestro
```

Or build the Windows exe with `build.bat`.

Happy playing!
