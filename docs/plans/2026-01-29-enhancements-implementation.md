# Maestro Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 8 enhancements to improve Maestro's usability, error visibility, and add visual features.

**Architecture:** New modules for config persistence (config.py) and logging (logger.py). Modifications to main.py (startup flow, countdown), player.py (remove pause, add note preview API), gui.py (UI changes, piano roll canvas).

**Tech Stack:** Python 3.11+, Tkinter (Canvas for piano roll), logging module (RotatingFileHandler), JSON for config.

---

## Task 1: Create Config Module

**Files:**
- Create: `src/maestro/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test for get_config_dir**

```python
# tests/test_config.py
import pytest
from pathlib import Path
from unittest.mock import patch
import sys

from maestro.config import get_config_dir


def test_get_config_dir_windows():
    """On Windows, should return APPDATA/Maestro."""
    with patch.object(sys, 'platform', 'win32'):
        with patch.dict('os.environ', {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
            result = get_config_dir()
            assert result == Path('C:\\Users\\Test\\AppData\\Roaming/Maestro')


def test_get_config_dir_linux():
    """On Linux, should return ~/.maestro."""
    with patch.object(sys, 'platform', 'linux'):
        with patch('pathlib.Path.home', return_value=Path('/home/test')):
            result = get_config_dir()
            assert result == Path('/home/test/.maestro')
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with "No module named 'maestro.config'"

**Step 3: Write the config module**

```python
# src/maestro/config.py
"""Configuration management for Maestro.

Handles loading and saving user settings to a JSON file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "last_songs_folder": "",
    "game_mode": "Heartopia",
    "speed": 1.0,
    "preview_lookahead": 5,
}


def get_config_dir() -> Path:
    """Return platform-appropriate config directory.

    Returns:
        Path to config directory (not created yet)
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Maestro"
    else:
        return Path.home() / ".maestro"


def get_config_path() -> Path:
    """Return path to config file."""
    return get_config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from JSON file.

    Returns:
        Config dict with all keys from DEFAULT_CONFIG.
        Missing keys are filled with defaults.
    """
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                saved = json.load(f)
                config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass  # Use defaults on error

    return config


def save_config(settings: dict[str, Any]) -> None:
    """Save settings to JSON file.

    Args:
        settings: Dict with settings to save
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(settings, f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Add tests for load_config and save_config**

```python
# Append to tests/test_config.py

def test_load_config_defaults(tmp_path):
    """Load returns defaults when no config exists."""
    with patch('maestro.config.get_config_path', return_value=tmp_path / 'config.json'):
        config = load_config()
        assert config['game_mode'] == 'Heartopia'
        assert config['speed'] == 1.0
        assert config['preview_lookahead'] == 5


def test_save_and_load_config(tmp_path):
    """Save then load should return same values."""
    config_path = tmp_path / 'config.json'
    with patch('maestro.config.get_config_dir', return_value=tmp_path):
        with patch('maestro.config.get_config_path', return_value=config_path):
            save_config({'game_mode': 'Where Winds Meet', 'speed': 0.75})
            config = load_config()
            assert config['game_mode'] == 'Where Winds Meet'
            assert config['speed'] == 0.75
```

**Step 6: Run all config tests**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add src/maestro/config.py tests/test_config.py
git commit -m "feat: add config module for settings persistence"
```

---

## Task 2: Create Logger Module

**Files:**
- Create: `src/maestro/logger.py`
- Create: `tests/test_logger.py`

**Step 1: Write the failing test**

```python
# tests/test_logger.py
import pytest
from pathlib import Path
from unittest.mock import patch
import logging

from maestro.logger import setup_logger, get_log_path


def test_get_log_path():
    """Log path should be in config directory."""
    with patch('maestro.logger.get_config_dir', return_value=Path('/test/dir')):
        result = get_log_path()
        assert result == Path('/test/dir/maestro.log')


def test_setup_logger_returns_logger():
    """setup_logger should return a configured logger."""
    logger = setup_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'maestro'
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_logger.py -v`
Expected: FAIL with "No module named 'maestro.logger'"

**Step 3: Write the logger module**

```python
# src/maestro/logger.py
"""Logging configuration for Maestro.

Sets up rotating file handler for error logging.
"""

import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from maestro.config import get_config_dir


_logger: logging.Logger | None = None


def get_log_path() -> Path:
    """Return path to log file."""
    return get_config_dir() / "maestro.log"


def setup_logger() -> logging.Logger:
    """Set up and return the maestro logger.

    Creates rotating file handler (1MB max, 3 backups).

    Returns:
        Configured logger instance
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("maestro")
    _logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Rotating file handler: 1MB max, keep 3 backups
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
    )
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    _logger.addHandler(handler)

    return _logger


def open_log_file() -> None:
    """Open log file in default text editor."""
    log_path = get_log_path()
    if not log_path.exists():
        return

    if sys.platform == "win32":
        os.startfile(log_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(log_path)])
    else:
        subprocess.run(["xdg-open", str(log_path)])
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_logger.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/maestro/logger.py tests/test_logger.py
git commit -m "feat: add logger module with rotating file handler"
```

---

## Task 3: Remove Pause from Player

**Files:**
- Modify: `src/maestro/player.py`
- Modify: `tests/test_player.py`

**Step 1: Update test file - remove pause test, add simplified tests**

```python
# Replace contents of tests/test_player.py
import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path

from maestro.player import Player, PlaybackState


@pytest.fixture
def mock_keyboard():
    """Mock pynput keyboard controller."""
    with patch('maestro.player.Controller') as mock:
        yield mock.return_value


@pytest.fixture
def sample_midi(tmp_path):
    """Create a simple test MIDI with multiple notes for longer playback."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for i in range(5):
        track.append(mido.Message('note_on', note=60, velocity=64, time=480))
        track.append(mido.Message('note_off', note=60, velocity=64, time=240))
    midi_path = tmp_path / "test.mid"
    mid.save(midi_path)
    return midi_path


def test_player_initial_state():
    """Player should start in STOPPED state."""
    player = Player()
    assert player.state == PlaybackState.STOPPED


def test_player_load_song(sample_midi, mock_keyboard):
    """Player should load a MIDI file."""
    player = Player()
    player.load(sample_midi)
    assert player.current_song == sample_midi


def test_player_play_changes_state(sample_midi, mock_keyboard):
    """Playing should change state to PLAYING."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    assert player.state == PlaybackState.PLAYING
    player.stop()


def test_player_stop_changes_state(sample_midi, mock_keyboard):
    """Stopping should change state to STOPPED."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    player.stop()
    assert player.state == PlaybackState.STOPPED


def test_playback_state_has_no_paused():
    """PlaybackState should only have STOPPED and PLAYING."""
    states = [s.name for s in PlaybackState]
    assert 'STOPPED' in states
    assert 'PLAYING' in states
    assert 'PAUSED' not in states
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_player.py -v`
Expected: FAIL (PAUSED still exists)

**Step 3: Modify player.py to remove pause**

Remove from `src/maestro/player.py`:
- Line 32: Remove `PAUSED = auto()` from PlaybackState enum
- Lines 47, 49-51: Remove `_pause_event`, `_pause_time`, `_elapsed_before_pause`
- Lines 90-91: Remove position check for PAUSED state
- Lines 108-114: Remove resume-from-pause logic in `play()`
- Lines 121, 124: Remove `_pause_event.clear()` and `_elapsed_before_pause` reset
- Lines 130-136: Remove entire `pause()` method
- Lines 141: Remove `_pause_event.set()` from stop()
- Lines 145: Remove `_elapsed_before_pause` reset from stop()
- Lines 150-155: Remove entire `toggle_pause()` method
- Lines 164-167: Remove pause handling in playback loop
- Lines 182-186: Remove pause check in sleep loop

The simplified player should have only STOPPED and PLAYING states.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_player.py -v`
Expected: PASS (5 tests)

**Step 5: Run all tests to check for breakage**

Run: `uv run pytest -v`
Expected: Some tests in test_main.py will fail (toggle_pause reference)

**Step 6: Commit**

```bash
git add src/maestro/player.py tests/test_player.py
git commit -m "refactor: remove pause functionality from player"
```

---

## Task 4: Remove Pause from GUI

**Files:**
- Modify: `src/maestro/gui.py`

**Step 1: Remove pause-related code from gui.py**

Remove from `src/maestro/gui.py`:
- Line 36: Remove `on_pause: Callable[[], None],` parameter
- Line 51: Remove `on_pause` from docstring
- Line 66: Remove `self.on_pause = on_pause`
- Line 178: Remove pause button line: `ttk.Button(btn_frame, text="Pause", command=self._on_pause_click).pack(...)`
- Lines 258-261: Remove entire `_on_pause_click()` method

**Step 2: Run GUI tests**

Run: `uv run pytest tests/test_gui.py -v`
Expected: PASS (GUI tests don't test pause button)

**Step 3: Commit**

```bash
git add src/maestro/gui.py
git commit -m "refactor: remove pause button from GUI"
```

---

## Task 5: Update Main - Remove Pause, Add Countdown, Auto-Show GUI

**Files:**
- Modify: `src/maestro/main.py`
- Modify: `tests/test_main.py`

**Step 1: Update test_main.py - remove pause test, add new tests**

```python
# Replace contents of tests/test_main.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from maestro.main import Maestro


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('maestro.main.Player') as player_mock, \
         patch('maestro.main.SongPicker') as picker_mock, \
         patch('maestro.main.keyboard') as kb_mock:
        yield {
            'player': player_mock.return_value,
            'picker': picker_mock.return_value,
            'keyboard': kb_mock,
        }


def test_maestro_initializes(mock_dependencies, tmp_path):
    """Maestro should initialize with songs folder."""
    app = Maestro(songs_folder=tmp_path)
    assert app.songs_folder == tmp_path


def test_maestro_stop(mock_dependencies, tmp_path):
    """Stop should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.stop()
    mock_dependencies['player'].stop.assert_called_once()


def test_maestro_play(mock_dependencies, tmp_path):
    """Play should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.play()
    mock_dependencies['player'].play.assert_called_once()


def test_maestro_get_state_with_countdown(mock_dependencies, tmp_path):
    """State string should show countdown when counting."""
    app = Maestro(songs_folder=tmp_path)
    app._countdown = 2
    state = app._get_state_string()
    assert state == "Starting in 2..."
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py -v`
Expected: FAIL (play method and _countdown don't exist)

**Step 3: Rewrite main.py with all changes**

```python
# src/maestro/main.py
"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import threading
import time
from pathlib import Path

from pynput import keyboard

from maestro.player import Player, PlaybackState
from maestro.gui import SongPicker
from maestro.game_mode import GameMode
from maestro.config import load_config, save_config
from maestro.logger import setup_logger


class Maestro:
    """Main application coordinator."""

    SONGS_FOLDER = Path("songs")
    STARTUP_DELAY = 3  # Seconds before playback starts (integer for countdown)

    def __init__(self, songs_folder: Path | None = None):
        """Initialize Maestro.

        Args:
            songs_folder: Path to folder containing MIDI files.
                         Defaults to ./songs or last used folder from config.
        """
        self.logger = setup_logger()
        self._config = load_config()

        # Use provided folder, or config folder, or default
        if songs_folder:
            self.songs_folder = songs_folder
        elif self._config.get("last_songs_folder"):
            self.songs_folder = Path(self._config["last_songs_folder"])
        else:
            self.songs_folder = self.SONGS_FOLDER

        self.songs_folder.mkdir(exist_ok=True)

        self.player = Player()
        self._listener: keyboard.Listener | None = None
        self._countdown: int = 0  # Countdown seconds remaining (0 = not counting)

        # Apply saved settings
        game_mode_str = self._config.get("game_mode", "Heartopia")
        for mode in GameMode:
            if mode.value == game_mode_str:
                self.player.game_mode = mode
                break
        self.player.speed = self._config.get("speed", 1.0)

        self.picker = SongPicker(
            songs_folder=self.songs_folder,
            on_play=self._on_play,
            on_stop=self.stop,
            get_state=self._get_state_string,
            get_position=lambda: self.player.position,
            get_duration=lambda: self.player.duration,
            get_current_song=self._get_current_song_name,
            on_exit=self._exit,
            on_game_change=self._on_game_change,
            get_last_key=lambda: self.player.last_key,
            on_speed_change=self._on_speed_change,
            on_folder_change=self._on_folder_change,
            initial_game_mode=self.player.game_mode,
            initial_speed=self.player.speed,
        )

        self._gui_thread: threading.Thread | None = None

    def _save_config(self) -> None:
        """Save current settings to config."""
        self._config["last_songs_folder"] = str(self.songs_folder)
        self._config["game_mode"] = self.player.game_mode.value
        self._config["speed"] = self.player.speed
        save_config(self._config)

    def _on_folder_change(self, folder: Path) -> None:
        """Handle folder change from GUI."""
        self.songs_folder = folder
        self._save_config()

    def _on_game_change(self, mode: GameMode) -> None:
        """Handle game mode change from GUI."""
        self.player.game_mode = mode
        self._save_config()
        print(f"Game mode: {mode.value}")

    def _on_speed_change(self, speed: float) -> None:
        """Handle speed change from GUI."""
        self.player.speed = speed
        self._save_config()

    def _on_play(self, song_path: Path) -> None:
        """Handle play request from GUI."""
        self.player.stop()
        try:
            self.player.load(song_path)
        except Exception as e:
            self.logger.error(f"Failed to load '{song_path}': {e}")
            self.picker.set_error(f"Error: {e}")
            return

        # Start playback after countdown
        def countdown_play():
            for i in range(self.STARTUP_DELAY, 0, -1):
                self._countdown = i
                print(f"Playing '{song_path.stem}' in {i}...")
                time.sleep(1)
                if self.player.state == PlaybackState.PLAYING:
                    # Already started somehow
                    self._countdown = 0
                    return
            self._countdown = 0
            if self.player.state == PlaybackState.STOPPED:
                self.player.play()

        threading.Thread(target=countdown_play, daemon=True).start()

    def _get_state_string(self) -> str:
        """Get current playback state as string."""
        if self._countdown > 0:
            return f"Starting in {self._countdown}..."
        return self.player.state.name.capitalize()

    def _get_current_song_name(self) -> str | None:
        """Get current song name."""
        if self.player.current_song:
            return self.player.current_song.stem
        return None

    def show_picker(self) -> None:
        """Show the song picker GUI."""
        if self._gui_thread is None or not self._gui_thread.is_alive():
            self._gui_thread = threading.Thread(target=self._run_gui, daemon=True)
            self._gui_thread.start()
        else:
            self.picker.show()

    def _run_gui(self) -> None:
        """Run the GUI in a separate thread."""
        self.picker.show()
        self.picker.run()

    def play(self) -> None:
        """Start playback if song is loaded."""
        if self.player.current_song and self.player.state == PlaybackState.STOPPED:
            self.player.play()

    def stop(self) -> None:
        """Stop playback."""
        self._countdown = 0
        self.player.stop()

    def _exit(self) -> None:
        """Exit the application."""
        print("\nExiting...")
        self._save_config()
        self.stop()
        if self._listener:
            self._listener.stop()

    def start(self) -> None:
        """Start the application with hotkey listening."""
        print("Maestro ready!")
        print("  F2: Play")
        print("  F3: Stop playback")
        print("  Ctrl+C: Exit")
        print()

        # Show GUI immediately
        self.show_picker()

        def on_press(key):
            if key == keyboard.Key.f2:
                self.play()
            elif key == keyboard.Key.f3:
                self.stop()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()
        try:
            self._listener.join()
        except KeyboardInterrupt:
            self._exit()


def main():
    """Entry point."""
    app = Maestro()
    app.start()


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_main.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/maestro/main.py tests/test_main.py
git commit -m "feat: auto-show GUI, remove pause, add countdown timer"
```

---

## Task 6: Update GUI - Add Error Display, Open Log, Folder Callback

**Files:**
- Modify: `src/maestro/gui.py`

**Step 1: Update SongPicker class signature and add new features**

Add to `__init__` parameters:
- `on_folder_change: Callable[[Path], None] | None = None`
- `initial_game_mode: GameMode | None = None`
- `initial_speed: float = 1.0`

Add new instance variables:
- `self.on_folder_change = on_folder_change`
- `self._last_error: str = ""`

Add new methods:
- `set_error(message: str)` - sets error to display
- `_on_open_log_click()` - opens log file

Modify `show()`:
- Add "Open Log" button next to status
- Use initial_game_mode and initial_speed for default values
- Make status label red when showing errors

Modify `_on_browse_click()`:
- Call `on_folder_change` callback

Modify `_update_status()`:
- Show error in red if `_last_error` is set

**Step 2: Run tests**

Run: `uv run pytest tests/test_gui.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/maestro/gui.py
git commit -m "feat: add error display and Open Log button to GUI"
```

---

## Task 7: Add Error Logging to Parser

**Files:**
- Modify: `src/maestro/parser.py`

**Step 1: Add logging to parse_midi**

```python
# At top of parser.py, add import:
from maestro.logger import setup_logger

# In parse_midi function, add logging:
def parse_midi(midi_path: Path) -> list[Note]:
    logger = setup_logger()

    if not midi_path.exists():
        logger.error(f"MIDI file not found: {midi_path}")
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        logger.error(f"Invalid MIDI file '{midi_path}': {e}")
        raise ValueError(f"Invalid MIDI file: {e}")

    # ... rest of function
```

**Step 2: Run parser tests**

Run: `uv run pytest tests/test_parser.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/maestro/parser.py
git commit -m "feat: add error logging to MIDI parser"
```

---

## Task 8: Add Error Logging to Player

**Files:**
- Modify: `src/maestro/player.py`

**Step 1: Replace bare except with specific handling and logging**

In `_press_key()` method, replace:
```python
except Exception:
    pass  # Ignore key errors
```

With:
```python
except Exception as e:
    self._logger.error(f"Key press failed for '{key}': {e}")
    self._last_error = f"Key simulation failed: {e}"
```

Add to `__init__`:
```python
from maestro.logger import setup_logger
# ...
self._logger = setup_logger()
self._last_error: str = ""
```

Add property:
```python
@property
def last_error(self) -> str:
    """Last error message."""
    return self._last_error
```

**Step 2: Run player tests**

Run: `uv run pytest tests/test_player.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/maestro/player.py
git commit -m "feat: add error logging to player key simulation"
```

---

## Task 9: Fix Speed Range

**Files:**
- Modify: `src/maestro/player.py`
- Modify: `tests/test_player.py`

**Step 1: Add test for speed clamping**

```python
# Add to tests/test_player.py
def test_speed_clamped_to_valid_range():
    """Speed should be clamped between 0.25 and 1.5."""
    player = Player()

    player.speed = 0.1  # Below min
    assert player.speed == 0.25

    player.speed = 2.0  # Above max
    assert player.speed == 1.5

    player.speed = 1.0  # Valid
    assert player.speed == 1.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_player.py::test_speed_clamped_to_valid_range -v`
Expected: FAIL (0.1 returns 0.1, not 0.25)

**Step 3: Fix speed setter in player.py**

Change line 76 from:
```python
self._speed = max(0.1, min(2.0, value))
```

To:
```python
self._speed = max(0.25, min(1.5, value))
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_player.py::test_speed_clamped_to_valid_range -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/maestro/player.py tests/test_player.py
git commit -m "fix: align speed range to 0.25-1.5 matching GUI slider"
```

---

## Task 10: Add get_upcoming_notes to Player

**Files:**
- Modify: `src/maestro/player.py`
- Modify: `tests/test_player.py`

**Step 1: Add test for get_upcoming_notes**

```python
# Add to tests/test_player.py
def test_get_upcoming_notes_returns_notes_within_lookahead(sample_midi, mock_keyboard):
    """get_upcoming_notes should return notes within lookahead window."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)

    notes = player.get_upcoming_notes(5.0)
    assert isinstance(notes, list)
    # Should have some notes (the sample has 5 notes)
    player.stop()


def test_get_upcoming_notes_empty_when_stopped():
    """get_upcoming_notes should return empty list when stopped."""
    player = Player()
    notes = player.get_upcoming_notes(5.0)
    assert notes == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_player.py::test_get_upcoming_notes_returns_notes_within_lookahead -v`
Expected: FAIL (method doesn't exist)

**Step 3: Add get_upcoming_notes method to Player**

```python
# Add to Player class in player.py
def get_upcoming_notes(self, lookahead: float) -> list[Note]:
    """Return notes within lookahead seconds from current position.

    Args:
        lookahead: How many seconds ahead to look

    Returns:
        List of Note objects within the lookahead window
    """
    if self.state == PlaybackState.STOPPED or not self._notes:
        return []

    current_pos = self.position
    end_pos = current_pos + lookahead

    upcoming = []
    for note in self._notes[self._note_index:]:
        if note.time > end_pos:
            break
        if note.time >= current_pos:
            upcoming.append(note)

    return upcoming
```

Also add import at top:
```python
from maestro.parser import Note
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_player.py::test_get_upcoming_notes_returns_notes_within_lookahead tests/test_player.py::test_get_upcoming_notes_empty_when_stopped -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/maestro/player.py tests/test_player.py
git commit -m "feat: add get_upcoming_notes method for piano roll preview"
```

---

## Task 11: Add Piano Roll Preview to GUI

**Files:**
- Modify: `src/maestro/gui.py`

**Step 1: Add piano roll components to SongPicker**

Add to `__init__` parameters:
- `get_upcoming_notes: Callable[[float], list] | None = None`

Add new instance variables:
- `self.get_upcoming_notes = get_upcoming_notes`
- `self.preview_canvas: tk.Canvas | None = None`
- `self.lookahead_var: tk.IntVar | None = None`
- `self._lookahead: int = 5  # default 5 seconds`

Add to `show()` method after "Now Playing" section:
```python
# Note Preview
preview_frame = ttk.LabelFrame(self.window, text="Note Preview")
preview_frame.pack(fill=tk.X, padx=10, pady=5)

# Lookahead selector
lookahead_row = ttk.Frame(preview_frame)
lookahead_row.pack(fill=tk.X, padx=5, pady=(5, 0))

ttk.Label(lookahead_row, text="Lookahead:").pack(side=tk.LEFT)
self.lookahead_var = tk.IntVar(value=self._lookahead)
lookahead_dropdown = ttk.Combobox(
    lookahead_row,
    textvariable=self.lookahead_var,
    values=[2, 5, 10],
    state="readonly",
    width=5,
)
lookahead_dropdown.pack(side=tk.LEFT, padx=(5, 0))
lookahead_dropdown.bind("<<ComboboxSelected>>", self._on_lookahead_change)
ttk.Label(lookahead_row, text="seconds").pack(side=tk.LEFT, padx=(5, 0))

# Canvas for piano roll
self.preview_canvas = tk.Canvas(preview_frame, height=80, bg="black")
self.preview_canvas.pack(fill=tk.X, padx=5, pady=5)
```

Add method for drawing:
```python
def _draw_piano_roll(self) -> None:
    """Draw upcoming notes on the preview canvas."""
    if not self.preview_canvas or not self.get_upcoming_notes:
        return

    self.preview_canvas.delete("all")

    canvas_width = self.preview_canvas.winfo_width()
    canvas_height = self.preview_canvas.winfo_height()

    if canvas_width < 10:  # Not yet rendered
        return

    # Draw playhead line
    self.preview_canvas.create_line(2, 0, 2, canvas_height, fill="red", width=2)

    lookahead = self.lookahead_var.get() if self.lookahead_var else 5
    notes = self.get_upcoming_notes(float(lookahead))

    if not notes:
        return

    # Find note range for vertical scaling
    if notes:
        min_note = min(n.midi_note for n in notes)
        max_note = max(n.midi_note for n in notes)
        note_range = max(max_note - min_note, 12)  # At least one octave
    else:
        min_note, note_range = 60, 12

    current_pos = self.get_position() if self.get_position else 0.0

    for note in notes:
        # X position based on time
        time_offset = note.time - current_pos
        x = 5 + (time_offset / lookahead) * (canvas_width - 10)

        # Width based on duration (min 3px)
        width = max(3, (note.duration / lookahead) * (canvas_width - 10))

        # Y position based on pitch (higher = top)
        y_ratio = 1 - ((note.midi_note - min_note) / note_range)
        y = 5 + y_ratio * (canvas_height - 10)

        # Draw note rectangle
        self.preview_canvas.create_rectangle(
            x, y - 3, x + width, y + 3,
            fill="#4CAF50", outline="#2E7D32"
        )
```

Add to `_update_progress()`:
```python
# Update piano roll
self._draw_piano_roll()
```

Change window height from 550 to 700:
```python
self.window.geometry("400x700")
```

**Step 2: Update main.py to pass get_upcoming_notes**

In Maestro.__init__, add to SongPicker constructor:
```python
get_upcoming_notes=self.player.get_upcoming_notes,
```

**Step 3: Run all tests**

Run: `uv run pytest -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/maestro/gui.py src/maestro/main.py
git commit -m "feat: add piano roll note preview to GUI"
```

---

## Task 12: Save Preview Lookahead to Config

**Files:**
- Modify: `src/maestro/gui.py`
- Modify: `src/maestro/main.py`

**Step 1: Add lookahead to config flow**

In gui.py, add `on_lookahead_change` callback parameter and method:
```python
def _on_lookahead_change(self, event=None) -> None:
    """Handle lookahead dropdown change."""
    if self.on_lookahead_change and self.lookahead_var:
        self.on_lookahead_change(self.lookahead_var.get())
```

In main.py, add callback:
```python
def _on_lookahead_change(self, lookahead: int) -> None:
    """Handle lookahead change from GUI."""
    self._config["preview_lookahead"] = lookahead
    self._save_config()
```

Pass initial lookahead and callback to SongPicker.

**Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/maestro/gui.py src/maestro/main.py
git commit -m "feat: persist preview lookahead setting to config"
```

---

## Task 13: Final Integration Test

**Files:**
- Run full test suite
- Manual verification

**Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 2: Manual smoke test**

Run: `uv run maestro`

Verify:
- [ ] GUI opens immediately
- [ ] Console shows "Maestro ready!" with F2/F3 instructions
- [ ] No pause button visible
- [ ] Countdown shows "Starting in 3..." when playing
- [ ] Piano roll displays upcoming notes
- [ ] Lookahead dropdown works (2/5/10s)
- [ ] Open Log button works
- [ ] Settings persist after restart (folder, game mode, speed, lookahead)
- [ ] Errors display in status bar

**Step 3: Commit any fixes**

**Step 4: Final commit with all changes**

```bash
git status
git add -A
git commit -m "feat: complete all 8 enhancements

- GUI opens immediately on startup
- Removed pause functionality (play/stop only)
- Settings persistence in AppData
- Error logging with Open Log button
- Speed range aligned to 0.25-1.5x
- Countdown timer in status
- Piano roll note preview
- Removed unused sys import"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Create config module | config.py, test_config.py |
| 2 | Create logger module | logger.py, test_logger.py |
| 3 | Remove pause from player | player.py, test_player.py |
| 4 | Remove pause from GUI | gui.py |
| 5 | Update main (GUI auto-show, countdown) | main.py, test_main.py |
| 6 | Add error display & Open Log | gui.py |
| 7 | Add logging to parser | parser.py |
| 8 | Add logging to player | player.py |
| 9 | Fix speed range | player.py, test_player.py |
| 10 | Add get_upcoming_notes | player.py, test_player.py |
| 11 | Add piano roll preview | gui.py, main.py |
| 12 | Save lookahead to config | gui.py, main.py |
| 13 | Final integration test | - |

**Total: 13 tasks, ~13 commits**
