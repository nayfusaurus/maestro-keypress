# CLAUDE.md

## Project Overview

Maestro is a Python CLI app that auto-plays MIDI songs on Heartopia's in-game piano by simulating keyboard presses. Users press F1 to open a song picker, select a MIDI file, and the app plays it by pressing the appropriate keys.

## Tech Stack

- Python 3.11+
- uv (package manager)
- mido (MIDI parsing)
- pynput (keyboard simulation + global hotkeys)
- tkinter (GUI)

## Architecture

```
Maestro (main.py) - coordinates everything
    ├── Player (player.py) - playback engine, runs in background thread
    │       ├── parser.py - extracts notes from MIDI files
    │       └── keymap.py - maps MIDI notes to Heartopia keys
    └── SongPicker (gui.py) - Tkinter GUI for song selection
```

## Key Files

- `src/maestro/keymap.py` - MIDI note to keyboard key mapping for Heartopia's 3-octave piano
- `src/maestro/parser.py` - Parses MIDI files into Note objects with timing
- `src/maestro/player.py` - Threaded playback engine with play/pause/stop
- `src/maestro/gui.py` - Tkinter song picker window
- `src/maestro/main.py` - Main coordinator with hotkey handling

## Commands

```bash
uv run maestro          # Run the app
uv run pytest -v        # Run tests
uv sync                 # Install dependencies
```

## Hotkeys

- F1: Open song picker
- F2: Play/Pause toggle
- F3: Stop playback
- Ctrl+C: Exit app

## Testing

24 tests across 6 test files covering all modules. Run with `uv run pytest -v`.

## Design Decisions

- **3-second startup delay**: After selecting a song, playback waits 3 seconds so user can switch to Heartopia
- **Transposition**: Notes outside the 3-octave range (MIDI 48-83) are transposed into range
- **Threading**: Player runs in daemon thread; GUI runs in separate thread
- **Minimum keypress timing**: 50ms minimum between keypresses for game registration
