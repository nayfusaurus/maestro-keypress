# CLAUDE.md

## Project Overview

Maestro is a Python CLI app that auto-plays MIDI songs on in-game pianos by simulating keyboard presses. Supports Heartopia and Where Winds Meet. Users press F1 to open a song picker, select a MIDI file, and the app plays it by pressing the appropriate keys.

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
    │       ├── keymap.py - maps MIDI notes to Heartopia keys
    │       ├── keymap_wwm.py - maps MIDI notes to Where Winds Meet keys
    │       └── game_mode.py - GameMode enum for game selection
    └── SongPicker (gui.py) - Tkinter GUI for song selection
```

## Key Files

- `src/maestro/keymap.py` - MIDI note to keyboard key mapping for Heartopia's 3-octave piano
- `src/maestro/keymap_wwm.py` - Where Winds Meet key mapping with Shift modifiers
- `src/maestro/game_mode.py` - GameMode enum for game selection
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

75 tests across multiple test files covering all modules. Run with `uv run pytest -v`.

## GUI Features

- **Search bar**: Filter songs by name in real-time
- **Progress bar**: Visual playback position with time display (M:SS / M:SS)
- **Now Playing panel**: Shows current song name
- **Browse button**: Change songs folder without restarting

## Design Decisions

- **3-second startup delay**: After selecting a song, playback waits 3 seconds so user can switch to Heartopia
- **Transposition**: Notes outside the 4-octave range (MIDI 36-84) are transposed into range
- **Threading**: Player runs in daemon thread; GUI runs in separate thread
- **Minimum keypress timing**: 50ms minimum between keypresses for game registration

## Building Windows Exe

pynput requires native Windows to capture global hotkeys (won't work in WSL).

**Option 1:** Double-click `build.bat`

**Option 2:** Run manually:

```powershell
pip install mido pynput pyinstaller
pyinstaller Maestro.spec --noconfirm
```

Build config is in `Maestro.spec`. Output: `dist/Maestro.exe`
