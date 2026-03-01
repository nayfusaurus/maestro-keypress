# CLAUDE.md

## Project Overview

Maestro is a Python CLI app that auto-plays MIDI songs on in-game pianos by simulating keyboard presses. Supports Heartopia and Where Winds Meet. The GUI opens automatically on startup. Users select a MIDI file, and after a 3-second countdown, the app plays it by pressing the appropriate keys.

## Tech Stack

- Python 3.11+
- uv (package manager)
- mido (MIDI parsing)
- pynput (keyboard simulation + global hotkeys)
- pydirectinput (DirectInput keyboard simulation for WWM)
- PySide6 (Qt6 GUI with dark/light theme)
- yt-dlp (YouTube audio download)
- basic-pitch (audio-to-MIDI transcription, ONNX backend)
- onnxruntime (ML inference for basic-pitch)
- opencv-python-headless (Synthesia frame analysis)

## Architecture

```text
Maestro (main.py) - coordinates everything, Qt event loop on main thread
    ├── Player (player.py) - event-driven playback engine with caching
    │       ├── parser.py - MIDI parsing with multi-tempo support
    │       ├── keymap.py - 22-key Heartopia mapping (C3-C6)
    │       ├── keymap_15_double.py - 15-key double row mapping
    │       ├── keymap_15_triple.py - 15-key triple row mapping
    │       ├── keymap_drums.py - 8-key drums mapping (MIDI 60-67)
    │       ├── keymap_xylophone.py - 8-key xylophone mapping (MIDI 60-72, natural notes)
    │       ├── keymap_wwm.py - Where Winds Meet mapping
    │       ├── key_layout.py - KeyLayout enum
    │       └── game_mode.py - GameMode enum
    ├── gui/ - PySide6 GUI package (signal/slot architecture, dark theme)
    │       ├── __init__.py - public API exports
    │       ├── main_window.py - MainWindow(QMainWindow), IconRail + QStackedWidget multi-page shell
    │       ├── signals.py - MaestroSignals(QObject) with all Signal definitions
    │       ├── icon_rail.py - 56px vertical icon sidebar with QPainter-drawn icons
    │       ├── toggle_switch.py - Animated iOS-style toggle switch (40x22px)
    │       ├── exit_dialog.py - Modal exit confirmation dialog
    │       ├── song_list.py - SongListWidget with custom delegate (rich two-line items)
    │       ├── piano_roll.py - PianoRollWidget (custom paintEvent, accent-colored)
    │       ├── progress_panel.py - NowPlayingPanel (transport-style, thin progress bar)
    │       ├── controls_panel.py - Play/Stop/Favorite (primary/secondary/ghost tiers)
    │       ├── import_panel.py - ImportPanel (URL input bar for YouTube)
    │       ├── splash.py - SplashScreen (loading screen with progress bar)
    │       ├── workers.py - ValidationWorker, UpdateCheckWorker, ImportWorker, DemucsDownloadWorker
    │       ├── constants.py - APP_VERSION, BINDABLE_KEYS, BINDABLE_KEYS_QT
    │       ├── theme.py - Dual theme (dark/light), design tokens, QSS builder
    │       ├── utils.py - get_songs_from_folder(), format_time(), center_dialog(), check_hotkey_conflict()
    │       └── pages/ - Multi-page layout widgets
    │               ├── __init__.py
    │               ├── dashboard.py - Two-column dashboard (import + game settings + transport | song browser)
    │               ├── settings_page.py - Library, appearance, hotkeys, demucs, updates settings
    │               ├── info_page.py - About card + disclaimer card with first-launch accept flow
    │               └── log_page.py - Built-in error log viewer with auto-refresh
    ├── importers/ - URL import modules
    │       ├── __init__.py
    │       ├── youtube.py - YouTube audio download + MIDI transcription
    │       └── synthesia.py - Synthesia visual detection (OpenCV)
    ├── config.py - settings persistence with validation
    └── logger.py - rotating file logger
```

## Key Files

- `src/maestro/keymap.py` - MIDI note to keyboard key mapping for Heartopia's 22-key piano (C3-C6)
- `src/maestro/keymap_wwm.py` - Where Winds Meet key mapping with Shift modifiers
- `src/maestro/keymap_15_double.py` - 15-key double row keymap (naturals only, C4-C6, keys A-J + Q-I)
- `src/maestro/keymap_15_triple.py` - 15-key triple row keymap (naturals only, C4-C6, keys Y-P / H-; / N-/)
- `src/maestro/keymap_drums.py` - 8-key drums keymap (chromatic MIDI 60-67, keys YUIO/HJKL, transpose/sharp disabled)
- `src/maestro/keymap_xylophone.py` - 8-key xylophone keymap (natural notes only MIDI 60-72, keys A-K, transpose/sharp disabled)
- `src/maestro/key_layout.py` - KeyLayout enum for key layout selection (KEYS_22, KEYS_15_DOUBLE, KEYS_15_TRIPLE, KEYS_DRUMS, KEYS_XYLOPHONE)
- `src/maestro/game_mode.py` - GameMode enum for game selection
- `src/maestro/parser.py` - Parses MIDI files into Note objects with multi-tempo support and MIDI info extraction
- `src/maestro/player.py` - Event-driven playback engine with chord support, focus detection, stuck key protection, and event caching
- `src/maestro/gui/` - PySide6 GUI package (signal/slot, dark theme, multi-page layout)
- `src/maestro/gui/main_window.py` - MainWindow(QMainWindow), thin shell: IconRail + QStackedWidget with 4 pages
- `src/maestro/gui/icon_rail.py` - 56px vertical icon sidebar with QPainter-drawn icons, page navigation, exit action
- `src/maestro/gui/toggle_switch.py` - Animated iOS-style toggle switch (40x22px, QPropertyAnimation)
- `src/maestro/gui/exit_dialog.py` - Modal exit confirmation dialog (320x160)
- `src/maestro/gui/pages/dashboard.py` - Two-column dashboard: fixed 400px left (import + game settings + transport) + flexible right (song browser)
- `src/maestro/gui/pages/settings_page.py` - Library, appearance (theme/fullscreen/auto-minimize), hotkeys, demucs, updates
- `src/maestro/gui/pages/info_page.py` - About card + disclaimer card with first-launch accept/reject flow
- `src/maestro/gui/pages/log_page.py` - Built-in error log viewer with auto-refresh on page visit
- `src/maestro/gui/signals.py` - MaestroSignals with all Signal definitions (GUI↔backend communication)
- `src/maestro/gui/splash.py` - SplashScreen with progress bar (shown during startup, no maestro imports)
- `src/maestro/gui/workers.py` - ValidationWorker, UpdateCheckWorker, ImportWorker, DemucsDownloadWorker (QThread)
- `src/maestro/gui/import_panel.py` - Compact URL input bar for YouTube
- `src/maestro/gui/theme.py` - Dual theme system (dark/light), design tokens, QSS builder with Catppuccin palettes
- `src/maestro/importers/youtube.py` - YouTube audio download (yt-dlp) + MIDI transcription (basic-pitch) + piano isolation (demucs)
- `src/maestro/importers/synthesia.py` - Synthesia visual detection via OpenCV frame analysis
- `src/maestro/main.py` - Main coordinator with Qt event loop, signal/slot connections, QTimer state pushes
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

448 tests across multiple test files covering all modules. Run with `uv run pytest -v`. 2 tests skipped (Windows-only focus detection).

## GUI Features

- **Splash screen**: Loading screen with progress bar appears immediately on launch, closes when main window is ready
- **Auto-open**: GUI opens immediately on startup
- **Icon rail navigation**: 56px vertical icon sidebar with QPainter-drawn icons (home, gear, info, document) + exit action pinned to bottom
- **Multi-page layout**: QStackedWidget with 4 pages: Dashboard, Settings, Info (About + Disclaimer), Error Log
- **Dashboard page**: Two-column layout with fixed 400px left (import + game settings + transport) + flexible right (filter + refresh + song list)
- **Settings page**: Library folder, appearance (dark/light theme, fullscreen, auto-minimize toggles), hotkey remapping, demucs management, update checker
- **Info page**: About card (version, description, Ko-fi link) + disclaimer card with first-launch accept/reject flow
- **Error log page**: Built-in log viewer with auto-refresh on page visit, open-in-editor button
- **Exit dialog**: Modal confirmation dialog on exit icon click and window close
- **First-launch disclaimer**: Must accept disclaimer before accessing app; pages locked until accepted
- **Toggle switches**: Animated iOS-style toggle switches (40x22px, QPropertyAnimation) replacing checkboxes
- **Search bar**: Filter songs by name in real-time
- **Progress bar**: Transport-style thin (4px) progress bar with flanking time display (M:SS | bar | M:SS)
- **Now Playing panel**: Surface-card styled panel with song name and transport controls
- **Error display**: Shows errors prominently in red label above Now Playing panel
- **Browse button**: Change songs folder without restarting (in Settings page)
- **Speed slider**: Adjust playback speed (0.5x - 2.0x) with 0.1 snap increments
- **Countdown display**: Shows "Starting in 3..." before playback
- **Piano roll preview**: Optional lookahead panel showing upcoming notes (hidden by default)
- **Settings persistence**: Folder, game mode, speed, transpose, preview visibility, key layout, sharp handling, favorites, hotkeys, theme, disclaimer_accepted, fullscreen, auto-minimize saved between sessions
- **Keys layout dropdown**: 22-key, 15-key Double Row, 15-key Triple Row, Conga/Cajon (8-key) (Heartopia only, hidden for WWM)
- **Rich song list**: Two-line items with left accent bar (green/red/gray), favorite star, duration, BPM, note count via custom QStyledItemDelegate
- **MIDI validation**: Background scan with color-coded accent bars, incremental with mtime caching
- **Note compatibility**: Percentage of playable notes for current layout
- **Favorites**: Star toggle, favorites sorted first in the song list
- **Recently played**: Tracked (capped at 20)
- **Song finished notification**: Status label turns green, window title flashes, window restores from taskbar
- **Sharp handling**: Skip or snap setting for 15-key layouts (in Settings page)
- **Hotkey remapping**: Press-to-bind UI in Settings page for Play, Stop, Emergency Stop with conflict detection
- **Dark/Light theme**: Catppuccin Mocha (dark) and Catppuccin Latte (light) themes, switchable from Settings page
- **Song sorting**: Favorites > valid > pending > invalid (alphabetical within each group)
- **Multi-line song details**: Song info panel wraps long text across multiple lines
- **Auto-minimize on play**: Configurable toggle in Settings, window minimizes to taskbar when playback starts (primary monitor only)
- **Multi-monitor detection**: Skips auto-minimize when app is on secondary screen
- **Import panel**: Compact URL input bar for importing from YouTube (in Dashboard)
- **YouTube-to-MIDI**: Audio download via yt-dlp, transcription via basic-pitch, optional piano isolation via demucs
- **Synthesia detection**: OpenCV-based frame analysis for Synthesia video detection
- **Demucs management**: Download/remove piano isolation model from Settings page
- **Update notification badge**: Accent dot on Settings icon when update is available
- **Button hierarchy**: Primary (accent Play), Secondary (Stop), Ghost (Favorite, Refresh) button tiers
- **Design token system**: Centralized SPACING, RADIUS, FONT, COLORS tokens in theme.py — no inline styles
- **Window title per page**: "Maestro - Dashboard", "Maestro - Settings", etc.

## Design Decisions

- **Auto-open GUI**: GUI opens immediately on startup for faster workflow
- **No pause**: Simplified to play/stop only (no pause functionality)
- **3-second countdown**: After selecting a song, visual countdown before playback starts
- **Settings persistence**: Config stored in AppData (Windows) or ~/.maestro (Linux/Mac)
- **Error logging**: Rotating log file (1MB max, 3 backups) for debugging
- **Transposition**: Optional (off by default). When enabled, notes outside the playable range are transposed into range. When disabled, out-of-range notes are skipped. Disabled for drums layout.
- **Preview panel**: Optional piano roll showing upcoming notes (hidden by default)
- **Threading**: Qt event loop runs on main thread; pynput listener in background thread; player in daemon thread
- **Minimum keypress timing**: 50ms minimum between keypresses for game registration
- **Speed range**: 0.5x - 2.0x playback speed with 0.1 snap increments
- **DirectInput for WWM**: Where Winds Meet requires DirectInput; uses pydirectinput (Windows-only, falls back to pynput elsewhere)
- **Duration calculation**: Includes note duration so timer completes when last note finishes, not when it starts
- **Event-driven playback**: Each note becomes key-down at note.time and key-up at note.time+duration. Supports chords and respects MIDI durations.
- **Focus detection**: Windows-only via win32gui. Auto-pauses timeline when game window is not focused.
- **Stuck key protection**: atexit handler + signal handlers (SIGINT, SIGTERM) release all held keys on exit.
- **Config validation**: Invalid config values reset to defaults with warnings logged.
- **Multi-tempo MIDI**: Parser tracks tempo changes inline for correct timing across tempo changes.
- **Sharp handling**: 15-key layouts only have natural notes. Sharp notes can be skipped or snapped to nearest natural. Disabled for drums layout.
- **Max MIDI size**: 10MB limit to reject oversized files before parsing.
- **Auto-minimize**: Configurable toggle in Settings. Window iconifies when playback starts so the game window is unobstructed. Skipped on secondary monitors.
- **No always-on-top**: Window does not force itself above other windows.
- **Icon rail navigation**: 56px icon-only sidebar replaces menu bar. QPainter-drawn icons (no icon library dependency). Active page shown with 3px accent bar + accent icon color. Exit icon pinned to bottom turns red on hover.
- **Multi-page layout**: QStackedWidget with 4 pages. MainWindow is a thin shell that delegates all state to page widgets. Window title updates per page.
- **First-launch disclaimer flow**: On first launch, Info page is shown with Accept/Reject buttons. All other pages locked via set_disabled_pages() until disclaimer is accepted. Rejection closes the app.
- **Exit confirmation**: Modal dialog shown on both exit icon click and window close (closeEvent). Prevents accidental exits.
- **Toggle switches**: 40x22px animated toggle switches (QPropertyAnimation, 150ms InOutQuad) replace checkboxes for boolean settings. Colors from COLORS dict for theme consistency.
- **Dashboard two-column**: Fixed 400px left column (import card + game settings card + transport card) + flexible right column (filter + refresh + song list).
- **Settings page sections**: Library, Appearance (theme/fullscreen/auto-minimize), Hotkeys, Piano Isolation, Updates — each in a surface-card.
- **Built-in error log**: Log page with QTextEdit viewer, auto-refreshes on page visit via showEvent. Replaces File > Open Log menu action.
- **Update notification badge**: 6px accent dot on Settings icon when update is available, instead of dismissable banner.
- **ONNX inference backend**: basic-pitch supports TF/TFLite/ONNX/CoreML backends. ONNX Runtime is used for PyInstaller builds (~200MB vs TF's ~1.5GB). TF is excluded from the bundle; basic-pitch auto-detects ONNX at runtime via try/except ImportError.
- **Demucs optional**: Not bundled in exe (~1GB). Downloaded to ~/.maestro/models/ via Settings.
- **Window sizing**: 80% of primary screen, minimum 900x600, centered on launch.
- **Event caching**: Built events are cached and reused when only speed changes, invalidated on layout/transpose/sharp changes.
- **Incremental validation**: MIDI files are validated incrementally using mtime caching to avoid re-parsing unchanged files.
- **Drums layout**: Uses chromatic MIDI notes 60-67 (C4-G4, conga drums). Transpose and sharp handling are disabled for drums.
- **Xylophone layout**: Uses natural notes only (C major scale) MIDI 60-72 (C4-C5). Transpose and sharp handling are disabled for xylophone.
- **MIDI extensions**: Supports both `.mid` and `.midi` file extensions.
- **Hotkey conflict detection**: Warns users if they try to bind the same key to multiple actions.
- **Window restore on finish**: Window automatically restores from minimized state when song finishes.
- **Design tokens**: Centralized design system in theme.py with SPACING (4px grid), RADIUS, FONT scale, and COLORS (tonal surface hierarchy). All styling via QSS class/state selectors — no inline setStyleSheet calls.
- **Dual theme**: Dark (Catppuccin Mocha) and Light (Catppuccin Latte) themes. COLORS dict is mutable — updated in-place by apply_theme() so all modules (song_list delegate, piano_roll) automatically pick up current theme during paint.
- **Page-based settings**: All settings organized in dedicated Settings page with surface-card sections. Hotkey press-to-bind uses grabKeyboard() for reliable key capture.
- **Scrollable pages**: Page content wrapped in QScrollArea to handle smaller screens where cards might overflow.
- **Tonal surfaces**: Depth communicated through surface color hierarchy (surface0/1/2) instead of uniform borders. Borders used sparingly (focused inputs, list container only).
- **QSS class selectors**: Widgets styled via setProperty("class", "primary"/"ghost"/"caption"/"overline"/"title"/"surface-card"/"banner"/"key-badge") and dynamic state via setProperty("state", "finished"/"error") with unpolish/polish.
- **Custom item delegate**: SongListWidget uses QStyledItemDelegate for rich two-line items with accent bar, star, metadata — painted via QPainter, not QSS.
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

**ML Backend:** basic-pitch uses ONNX Runtime for audio-to-MIDI inference (not TensorFlow). TF is excluded from the bundle to keep exe size ~200-250MB. basic-pitch auto-detects the ONNX backend at runtime.
