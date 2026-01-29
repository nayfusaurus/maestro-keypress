# CLAUDE.md

## Project Overview

Maestro is a Python CLI app that auto-plays MIDI songs on in-game pianos by simulating keyboard presses. Supports Heartopia and Where Winds Meet. The GUI opens automatically on startup. Users select a MIDI file, and after a 3-second countdown, the app plays it by pressing the appropriate keys.

## Tech Stack

- Python 3.11+
- uv (package manager)
- mido (MIDI parsing)
- pynput (keyboard simulation + global hotkeys)
- pydirectinput (DirectInput keyboard simulation for WWM)
- tkinter (GUI)

## Architecture

```
Maestro (main.py) - coordinates everything
    ├── Player (player.py) - playback engine, runs in background thread
    │       ├── parser.py - extracts notes from MIDI files
    │       ├── keymap.py - maps MIDI notes to Heartopia keys
    │       ├── keymap_wwm.py - maps MIDI notes to Where Winds Meet keys
    │       └── game_mode.py - GameMode enum for game selection
    ├── SongPicker (gui.py) - Tkinter GUI for song selection
    ├── config.py - settings persistence (AppData/Maestro or ~/.maestro)
    └── logger.py - rotating file logger for error tracking
```

## Key Files

- `src/maestro/keymap.py` - MIDI note to keyboard key mapping for Heartopia's 3-octave piano
- `src/maestro/keymap_wwm.py` - Where Winds Meet key mapping with Shift modifiers
- `src/maestro/game_mode.py` - GameMode enum for game selection
- `src/maestro/parser.py` - Parses MIDI files into Note objects with timing
- `src/maestro/player.py` - Threaded playback engine with play/stop
- `src/maestro/gui.py` - Tkinter song picker window
- `src/maestro/main.py` - Main coordinator with hotkey handling
- `src/maestro/config.py` - JSON config management for settings persistence
- `src/maestro/logger.py` - Rotating file handler for error logging

## Commands

```bash
uv run maestro          # Run the app
uv run pytest -v        # Run tests
uv sync                 # Install dependencies
```

## Hotkeys

- F2: Play
- F3: Stop playback
- Ctrl+C: Exit app

## Testing

~100 tests across multiple test files covering all modules. Run with `uv run pytest -v`.

## GUI Features

- **Auto-open**: GUI opens immediately on startup
- **Search bar**: Filter songs by name in real-time
- **Progress bar**: Visual playback position with time display (M:SS / M:SS)
- **Now Playing panel**: Shows current song name
- **Browse button**: Change songs folder without restarting
- **Speed slider**: Adjust playback speed (0.25x - 1.5x)
- **Countdown display**: Shows "Starting in 3..." before playback
- **Error display**: Shows errors in red in status bar
- **Open Log button**: Opens log file for debugging
- **Settings persistence**: Folder, game mode, speed saved between sessions

## Design Decisions

- **Auto-open GUI**: GUI opens immediately on startup for faster workflow
- **No pause**: Simplified to play/stop only (no pause functionality)
- **3-second countdown**: After selecting a song, visual countdown before playback starts
- **Settings persistence**: Config stored in AppData (Windows) or ~/.maestro (Linux/Mac)
- **Error logging**: Rotating log file (1MB max, 3 backups) for debugging
- **Transposition**: Notes outside the playable range are transposed into range
- **Threading**: Player runs in daemon thread; GUI runs in separate thread
- **Minimum keypress timing**: 50ms minimum between keypresses for game registration
- **Speed range**: 0.25x - 1.5x playback speed
- **DirectInput for WWM**: Where Winds Meet requires DirectInput; uses pydirectinput (Windows-only, falls back to pynput elsewhere)

## Building Windows Exe

Requires native Windows to capture global hotkeys (won't work in WSL).

**Option 1:** Double-click `build.bat`

**Option 2:** Run manually:

```powershell
uv sync
uv add pyinstaller --dev
uv run pyinstaller Maestro.spec --noconfirm
```

Build config is in `Maestro.spec`. Output: `dist/Maestro.exe`
