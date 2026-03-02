# Changelog

All notable changes to Maestro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.2.0/).

## [2.0.0] - 2026-03-02

### Added

- **Once Human game mode**: Single-octave keys (Q-U naturals, 2/3/5/6/7 accidentals) with Shift/Ctrl octave switching for 36 chromatic notes (C3-B5)
- **WWM layout revamp**: 36-key layout uses Shift (C#/F#/G#) + Ctrl (Eb/Bb) modifiers; 21-key layout is naturals only with skip/snap sharp handling
- **MIDI post-processing pipeline**: 5-stage cleanup for YouTube transcriptions — velocity filtering, grace note removal, tied note merging, chord simplification, and beat quantization
- **YouTube import progress**: Real-time progress bar and status updates during download and transcription
- **Configurable countdown delay**: Customize the pre-playback countdown (1-10 seconds)
- **Import panel info tooltip**: Circled-i icon with guidance on best video types for transcription

### Changed

- **Speed slider range**: Changed from 0.25x-1.5x to 0.5x-2.0x
- **Import panel header**: Renamed to "YouTube to MIDI converter (Experimental)" with info tooltip
- **Dashboard layout dropdown**: Repopulates dynamically on game mode change (Heartopia/WWM/Once Human)
- **Once Human layout**: Hidden layout dropdown (single fixed layout, no sharp handling needed)
- **Removed demucs/isolate UI**: Removed piano isolation toggle from dashboard and demucs section from settings

### Fixed

- **Exit dialog theme**: Light theme now applies correctly to exit confirmation dialog
- **Word wrap**: Song name label and import header wrap properly instead of stretching the sidebar
- **Theme persistence**: Theme selection persists correctly across app restarts
- **App icon**: Set before splash screen for correct taskbar icon from launch

### Infrastructure

- **CI pipeline fixes**: Python 3.11 pinning, TF exclusion, mypy/ruff/pip-audit fixes, ffmpeg binary downloads
- **Dependencies updated**: bandit, ruff, pyinstaller, and transitive deps bumped to latest safe versions

### Tests

- Test suite expanded to 347 tests

## [1.5.0] - 2026-03-02

### Added

- **Multi-page GUI layout**: Icon sidebar navigation with Dashboard, Settings, Info, and Log pages
- **Dark/Light themes**: Catppuccin Mocha (dark) and Latte (light) with toggle switch in Settings
- **YouTube-to-MIDI import**: Paste a YouTube URL to download audio and transcribe to MIDI
  - Tuned basic-pitch parameters for piano accuracy (frequency bounds, lower thresholds)
  - Leading silence trimmed from transcribed MIDI files
- **Settings page**: Dedicated page with Library, Appearance, Hotkeys, and Updates cards
- **Info page**: About section with version, credits, Ko-fi link, and scrollable disclaimer
- **Log page**: Built-in error log viewer with refresh and open-in-editor buttons
- **Exit confirmation dialog**: Prevents accidental app closure
- **Toggle switches**: Custom ToggleSwitch widget replacing checkboxes for all boolean settings
- **First-launch disclaimer flow**: Accept/reject disclaimer before using the app
- **Splash screen**: Loading screen with progress bar shown during startup

### Changed

- **GUI framework**: Migrated from menu bar to icon sidebar navigation
- **Two-column dashboard**: Fixed 400px scrollable sidebar + flexible song list area
- **Window icon**: Fixed for PyInstaller builds (bundled icon.png, AppUserModelID for Windows taskbar)
- **Theme switching**: Fixed background not updating outside song list panel
- **Refresh button**: Made visible (no longer ghost style)

### Security

- **Bandit scan**: All 13 findings addressed with nosec annotations (all Low severity, intentional subprocess usage)
- **Ruff**: All lint checks passing

### Tests

- Test suite trimmed from 450 to 219 tests (removed low-value tests, kept meaningful coverage)

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
