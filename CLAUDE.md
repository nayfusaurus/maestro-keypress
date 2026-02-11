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
    ├── Player (player.py) - event-driven playback engine with caching
    │       ├── parser.py - MIDI parsing with multi-tempo support
    │       ├── keymap.py - 22-key Heartopia mapping (C3-C6)
    │       ├── keymap_15_double.py - 15-key double row mapping
    │       ├── keymap_15_triple.py - 15-key triple row mapping
    │       ├── keymap_drums.py - 8-key drums mapping (MIDI 60-67)
    │       ├── keymap_wwm.py - Where Winds Meet mapping
    │       ├── key_layout.py - KeyLayout enum
    │       └── game_mode.py - GameMode enum
    ├── SongPicker (gui.py) - Tkinter GUI with validation, favorites, hotkey remapping
    ├── config.py - settings persistence with validation
    └── logger.py - rotating file logger
```

## Key Files

- `src/maestro/keymap.py` - MIDI note to keyboard key mapping for Heartopia's 22-key piano (C3-C6)
- `src/maestro/keymap_wwm.py` - Where Winds Meet key mapping with Shift modifiers
- `src/maestro/keymap_15_double.py` - 15-key double row keymap (naturals only, C4-C6, keys A-J + Q-I)
- `src/maestro/keymap_15_triple.py` - 15-key triple row keymap (naturals only, C4-C6, keys Y-P / H-; / N-/)
- `src/maestro/keymap_drums.py` - 8-key drums keymap (chromatic MIDI 60-67, keys YUIO/HJKL, transpose/sharp disabled)
- `src/maestro/key_layout.py` - KeyLayout enum for key layout selection (KEYS_22, KEYS_15_DOUBLE, KEYS_15_TRIPLE, KEYS_DRUMS)
- `src/maestro/game_mode.py` - GameMode enum for game selection
- `src/maestro/parser.py` - Parses MIDI files into Note objects with multi-tempo support and MIDI info extraction
- `src/maestro/player.py` - Event-driven playback engine with chord support, focus detection, stuck key protection, and event caching
- `src/maestro/gui.py` - Tkinter song picker with validation, favorites, song info, hotkey remapping, incremental validation
- `src/maestro/main.py` - Main coordinator with configurable hotkeys, emergency stop, hotkey conflict detection, and layout/sharp handling callbacks
- `src/maestro/config.py` - JSON config management with validation and settings persistence
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

385 tests across multiple test files covering all modules. Run with `uv run pytest -v`. 2 tests skipped (Windows-only focus detection).

## GUI Features

- **Auto-open**: GUI opens immediately on startup
- **Menu bar**: File menu (Open Log, Settings, Exit) and Help menu (About, Disclaimer)
- **Settings dialog**: Modal dialog with transpose, preview panel toggles, sharp handling, and hotkey remapping
- **Search bar**: Filter songs by name in real-time
- **Progress bar**: Visual playback position with time display (M:SS / M:SS)
- **Now Playing panel**: Shows current song name
- **Error display**: Shows errors prominently in red label above Now Playing panel
- **Browse button**: Change songs folder without restarting
- **Speed slider**: Adjust playback speed (0.25x - 1.5x)
- **Countdown display**: Shows "Starting in 3..." before playback
- **Piano roll preview**: Optional lookahead panel showing upcoming notes (hidden by default)
- **Settings persistence**: Folder, game mode, speed, transpose, preview visibility, key layout, sharp handling, favorites, hotkeys saved between sessions
- **Keys layout dropdown**: 22-key, 15-key Double Row, 15-key Triple Row, Drums (8-key) (Heartopia only, hidden for WWM)
- **MIDI validation**: Background scan with green/red/gray status indicators (green=valid, red=invalid, gray=pending), incremental with mtime caching
- **Song info**: Duration, BPM, note count for selected song
- **Note compatibility**: Percentage of playable notes for current layout
- **Favorites**: Star toggle, favorites sorted first in the song list
- **Recently played**: Tracked (capped at 20)
- **Song finished notification**: Status label turns green, window title flashes, window restores from taskbar
- **Sharp handling**: Skip or snap setting for 15-key layouts (in Settings)
- **Hotkey remapping**: Press-to-bind UI in Settings for Play, Stop, Emergency Stop with conflict detection
- **Disclaimer**: ToS/disclaimer under Help menu
- **Song sorting**: Favorites > valid > pending > invalid (alphabetical within each group)
- **Multi-line song details**: Song info panel wraps long text across multiple lines
- **Auto-minimize on play**: Window minimizes to taskbar when playback starts

## Design Decisions

- **Auto-open GUI**: GUI opens immediately on startup for faster workflow
- **No pause**: Simplified to play/stop only (no pause functionality)
- **3-second countdown**: After selecting a song, visual countdown before playback starts
- **Settings persistence**: Config stored in AppData (Windows) or ~/.maestro (Linux/Mac)
- **Error logging**: Rotating log file (1MB max, 3 backups) for debugging
- **Transposition**: Optional (off by default). When enabled, notes outside the playable range are transposed into range. When disabled, out-of-range notes are skipped. Disabled for drums layout.
- **Preview panel**: Optional piano roll showing upcoming notes (hidden by default)
- **Threading**: Player runs in daemon thread; GUI runs in separate thread
- **Minimum keypress timing**: 50ms minimum between keypresses for game registration
- **Speed range**: 0.25x - 1.5x playback speed
- **DirectInput for WWM**: Where Winds Meet requires DirectInput; uses pydirectinput (Windows-only, falls back to pynput elsewhere)
- **Duration calculation**: Includes note duration so timer completes when last note finishes, not when it starts
- **Event-driven playback**: Each note becomes key-down at note.time and key-up at note.time+duration. Supports chords and respects MIDI durations.
- **Focus detection**: Windows-only via win32gui. Auto-pauses timeline when game window is not focused.
- **Stuck key protection**: atexit handler + signal handlers (SIGINT, SIGTERM) release all held keys on exit.
- **Config validation**: Invalid config values reset to defaults with warnings logged.
- **Multi-tempo MIDI**: Parser tracks tempo changes inline for correct timing across tempo changes.
- **Sharp handling**: 15-key layouts only have natural notes. Sharp notes can be skipped or snapped to nearest natural. Disabled for drums layout.
- **Max MIDI size**: 10MB limit to reject oversized files before parsing.
- **Auto-minimize**: Window iconifies when playback starts so the game window is unobstructed.
- **No always-on-top**: Window does not force itself above other windows.
- **Event caching**: Built events are cached and reused when only speed changes, invalidated on layout/transpose/sharp changes.
- **Incremental validation**: MIDI files are validated incrementally using mtime caching to avoid re-parsing unchanged files.
- **Drums layout**: Uses chromatic MIDI notes 60-67 (C4-G4, conga drums). Transpose and sharp handling are disabled for drums.
- **MIDI extensions**: Supports both `.mid` and `.midi` file extensions.
- **Hotkey conflict detection**: Warns users if they try to bind the same key to multiple actions.
- **Window restore on finish**: Window automatically restores from minimized state when song finishes.
- **Pinned dependencies**: All dependencies pinned to specific versions for reproducibility.
- **Code quality**: Linted with ruff and mypy in CI for type safety.
- **Security scanning**: pip-audit scans for vulnerabilities in dependencies on every CI run.
- **Release checksums**: SHA256 checksums provided for Windows exe releases.

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
