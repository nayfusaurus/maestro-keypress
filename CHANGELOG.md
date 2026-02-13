# Changelog

All notable changes to Maestro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.2.0/).

## [1.4.0] - 2026-02-13

### Added

- **Auto-update checker**: Checks GitHub for new releases on startup
  - Background check on app launch (non-blocking)
  - Update notification banner with "View Release" and "Dismiss" buttons
  - Manual check via Help → "Check for Updates..." menu item
  - Graceful error handling (fails silently if no internet)
- **App icon**: Custom icon for Windows .exe and GUI window
  - Multi-size .ico file for Windows builds
  - PNG icon displayed in window title bar

### Fixed

- **Keys dropdown bug**: Keys layout dropdown now correctly reappears when switching from WWM back to Heartopia

### Changed

- **README enhanced**: Professional layout with logo, badges, and better organization
  - Added maestro-logo with badges (CI, Python, License, Downloads, Claude)
  - Reorganized sections with collapsible details
  - Added Quick Start, Contributing, and Support sections

### Tests

- Test suite expanded to 368 tests (8 new tests for update checker)

## [1.3.0] - 2026-02-13

### Added

- **Xylophone (8-key) layout**: Natural notes only (C major scale) for Heartopia xylophone

### Changed

- **Drums layout renamed**: "Drums (8-key)" renamed to "Conga/Cajon (8-key)" for clarity

### Tests

- Test suite consolidated from 385 to 362 tests (removed redundant tests, improved coverage)

## [1.2.0] - 2026-02-11

### Added

- **Drums layout**: 8-key chromatic drum keymap (MIDI 60-67, keys YUIO/HJKL) for Heartopia
- **15-key layouts**: Double row (A-J / Q-I) and triple row (Y-P / H-; / N-/) natural-note keymaps
- **Event-driven playback**: Key-down/key-up events with chord support and MIDI duration tracking
- **Event caching**: Built events are cached and reused when only speed changes
- **Incremental MIDI validation**: Background scan with mtime caching to avoid re-parsing unchanged files
- **Sharp handling**: Skip or snap setting for 15-key layouts (configurable in Settings)
- **Hotkey remapping**: Press-to-bind UI in Settings for Play, Stop, and Emergency Stop keys
- **Hotkey conflict detection**: Warns when binding the same key to multiple actions
- **Song info panel**: Duration, BPM, and note count for selected song
- **Note compatibility**: Percentage of playable notes displayed for current layout
- **Favorites**: Star toggle with favorites sorted first in the song list
- **Recently played**: Tracks last 20 played songs
- **MIDI validation**: Background scan with green/red/gray status indicators
- **Settings dialog**: Modal dialog with transpose, preview panel toggles, sharp handling, and hotkey remapping
- **Piano roll preview**: Optional lookahead panel showing upcoming notes (hidden by default)
- **Search bar**: Filter songs by name in real-time
- **Progress bar**: Visual playback position with time display (M:SS / M:SS)
- **Now Playing panel**: Shows current song name during playback
- **Browse button**: Change songs folder without restarting
- **Speed slider**: Adjust playback speed (0.25x - 1.5x)
- **Countdown display**: Shows "Starting in 3..." before playback
- **Auto-minimize on play**: Window minimizes to taskbar when playback starts
- **Window restore on finish**: Window automatically restores when song finishes
- **Song finished notification**: Status label turns green, window title flashes
- **Song sorting**: Favorites > valid > pending > invalid (alphabetical within each group)
- **`.midi` file extension support**: Accepts both `.mid` and `.midi` files
- **Settings persistence**: All settings saved between sessions (JSON config)
- **Config validation**: Invalid config values reset to defaults with warnings logged
- **Error display**: Shows errors prominently in red label above Now Playing panel
- **Menu bar**: File menu (Open Log, Settings, Exit) and Help menu (About, Disclaimer)
- **Transposition**: Optional octave transposition for out-of-range notes (off by default, disabled for drums)
- **Error logging**: Rotating file handler (1MB max, 3 backups)
- **Stuck key protection**: atexit handler + signal handlers release all held keys on exit
- **Window focus detection**: Auto-pauses timeline when game window is not focused (Windows)
- **Multi-tempo MIDI support**: Parser tracks tempo changes inline for correct timing
- **10MB MIDI size limit**: Rejects oversized files before parsing
- **DirectInput for WWM**: Uses pydirectinput for Where Winds Meet (Windows-only, fallback to pynput)

### Changed

- Playback engine rewritten from sleep-based to event-driven architecture
- Minimum keypress timing set to 50ms for reliable game input detection
- Removed pause functionality (simplified to play/stop only)

### Security

- Dependencies pinned to exact versions for reproducibility
- pip-audit vulnerability scanning added to CI
- SHA256 checksums generated for Windows exe releases
- Ruff linting and mypy type checking enforced in CI

## [1.0.0] - 2026-01-28

### Added

- **Heartopia support**: 22-key piano keymap (C3-C6) with full chromatic mapping
- **Where Winds Meet support**: 36-key keymap with Shift modifier for sharps
- **Game mode selection**: Dropdown to switch between Heartopia and Where Winds Meet
- **GUI song picker**: Tkinter-based file browser with auto-open on startup
- **MIDI parsing**: Multi-track MIDI file support via mido
- **Keyboard simulation**: Key press/release via pynput
- **Global hotkeys**: F2 (Play), F3 (Stop), Ctrl+C (Exit)
- **Windows exe build**: PyInstaller spec for single-file distribution
