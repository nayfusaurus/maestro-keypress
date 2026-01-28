# Maestro Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python app that auto-plays MIDI songs on Heartopia's in-game piano via keyboard simulation.

**Architecture:** Background process with global hotkey listener. Alt+N opens Tkinter GUI to select songs. Player parses MIDI, converts notes to game keys, simulates keypresses with timing. State machine handles play/pause/stop.

**Tech Stack:** Python 3.11, uv, mido (MIDI), pynput (hotkeys/keyboard), tkinter (GUI)

---

## Task 1: Key Mapping Module

**Files:**
- Create: `src/maestro/keymap.py`
- Test: `tests/test_keymap.py`

**Step 1: Write the failing test**

Create `tests/test_keymap.py`:

```python
from maestro.keymap import midi_note_to_key, OCTAVE_HIGH, OCTAVE_MID, OCTAVE_LOW


def test_midi_note_to_key_middle_c():
    """Middle C (MIDI 60) should map to mid octave DO (Z key)."""
    key = midi_note_to_key(60)
    assert key == "z"


def test_midi_note_to_key_c_sharp():
    """C# (MIDI 61) should map to mid octave black key (S key)."""
    key = midi_note_to_key(61)
    assert key == "s"


def test_midi_note_to_key_high_octave():
    """Notes in high range map to high octave keys."""
    key = midi_note_to_key(72)  # C5
    assert key == "q"


def test_midi_note_to_key_low_octave():
    """Notes in low range map to low octave keys."""
    key = midi_note_to_key(48)  # C3
    assert key == "l"


def test_midi_note_to_key_transpose_too_high():
    """Notes above range get transposed down."""
    key = midi_note_to_key(96)  # C7 - way too high
    assert key in OCTAVE_HIGH.values()


def test_midi_note_to_key_transpose_too_low():
    """Notes below range get transposed up."""
    key = midi_note_to_key(24)  # C1 - way too low
    assert key in OCTAVE_LOW.values()


def test_octave_mappings_complete():
    """Each octave has 12 keys (7 white + 5 black)."""
    assert len(OCTAVE_HIGH) == 12
    assert len(OCTAVE_MID) == 12
    assert len(OCTAVE_LOW) == 12
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_keymap.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 3: Write the implementation**

Create `src/maestro/keymap.py`:

```python
"""Heartopia piano key mapping.

Maps MIDI note numbers to keyboard keys for Heartopia's 3-octave piano.
MIDI note 60 = Middle C = mid octave DO.
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
    6: "-",   # FA# (F#)
    7: "p",   # SOL (G)
    8: "=",   # SOL# (G#)  -- Note: may need adjustment based on actual game
    9: "[",   # LA (A)
    10: "=",  # LA# (A#)   -- Note: keyboard limitation, same as G#
    11: "]",  # SI (B)
}

# MIDI note ranges for each octave
MIDI_LOW_START = 48   # C3
MIDI_MID_START = 60   # C4 (Middle C)
MIDI_HIGH_START = 72  # C5
MIDI_HIGH_END = 83    # B5


def midi_note_to_key(midi_note: int) -> str:
    """Convert a MIDI note number to a Heartopia keyboard key.

    Args:
        midi_note: MIDI note number (0-127, where 60 = Middle C)

    Returns:
        Keyboard key character to press
    """
    # Transpose notes into our 3-octave range (48-83)
    while midi_note < MIDI_LOW_START:
        midi_note += 12
    while midi_note > MIDI_HIGH_END:
        midi_note -= 12

    # Determine which octave and note offset
    note_in_octave = midi_note % 12

    if midi_note >= MIDI_HIGH_START:
        return OCTAVE_HIGH[note_in_octave]
    elif midi_note >= MIDI_MID_START:
        return OCTAVE_MID[note_in_octave]
    else:
        return OCTAVE_LOW[note_in_octave]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_keymap.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/maestro/keymap.py tests/test_keymap.py
git commit -m "feat: add keymap module for MIDI-to-Heartopia key conversion"
```

---

## Task 2: MIDI Parser Module

**Files:**
- Create: `src/maestro/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/test_song.mid` (simple test MIDI)

**Step 1: Create a test MIDI file**

Create `tests/fixtures/test_song.mid` programmatically in the test:

```python
# tests/test_parser.py
import os
from pathlib import Path
import mido

from maestro.parser import parse_midi, Note


@pytest.fixture
def test_midi_path(tmp_path):
    """Create a simple test MIDI file."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Add some notes: C4, D4, E4 with timing
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=64, time=480))
    track.append(mido.Message('note_on', note=62, velocity=64, time=0))
    track.append(mido.Message('note_off', note=62, velocity=64, time=480))
    track.append(mido.Message('note_on', note=64, velocity=64, time=0))
    track.append(mido.Message('note_off', note=64, velocity=64, time=480))

    midi_path = tmp_path / "test_song.mid"
    mid.save(midi_path)
    return midi_path


def test_parse_midi_returns_notes(test_midi_path):
    """parse_midi should return a list of Note objects."""
    notes = parse_midi(test_midi_path)
    assert len(notes) == 3
    assert all(isinstance(n, Note) for n in notes)


def test_parse_midi_note_values(test_midi_path):
    """Notes should have correct MIDI values."""
    notes = parse_midi(test_midi_path)
    assert notes[0].midi_note == 60
    assert notes[1].midi_note == 62
    assert notes[2].midi_note == 64


def test_parse_midi_timing(test_midi_path):
    """Notes should have timing in seconds."""
    notes = parse_midi(test_midi_path)
    # First note starts at 0
    assert notes[0].time == 0.0
    # Subsequent notes have increasing times
    assert notes[1].time > notes[0].time
    assert notes[2].time > notes[1].time


def test_parse_midi_invalid_file():
    """Invalid file should raise ValueError."""
    import pytest
    with pytest.raises((ValueError, FileNotFoundError)):
        parse_midi(Path("/nonexistent/file.mid"))
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parser.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write the implementation**

Create `src/maestro/parser.py`:

```python
"""MIDI file parser for Maestro.

Parses MIDI files and extracts note events with timing.
"""

from dataclasses import dataclass
from pathlib import Path

import mido


@dataclass
class Note:
    """A note event with timing information."""
    midi_note: int  # MIDI note number (0-127)
    time: float     # Time in seconds from start of song
    duration: float # Duration in seconds


def parse_midi(midi_path: Path) -> list[Note]:
    """Parse a MIDI file and extract notes with timing.

    Args:
        midi_path: Path to the MIDI file

    Returns:
        List of Note objects sorted by time

    Raises:
        ValueError: If file is not a valid MIDI file
        FileNotFoundError: If file doesn't exist
    """
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        raise ValueError(f"Invalid MIDI file: {e}")

    notes = []
    # Track note_on events to calculate duration
    active_notes: dict[int, tuple[float, int]] = {}  # note -> (start_time, index)

    current_time = 0.0

    # Merge all tracks and process
    for msg in mido.merge_tracks(mid.tracks):
        # Convert delta time to seconds
        current_time += mido.tick2second(msg.time, mid.ticks_per_beat, get_tempo(mid))

        if msg.type == 'note_on' and msg.velocity > 0:
            # Note started
            active_notes[msg.note] = (current_time, len(notes))
            notes.append(Note(
                midi_note=msg.note,
                time=current_time,
                duration=0.0  # Will be updated on note_off
            ))
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Note ended
            if msg.note in active_notes:
                start_time, idx = active_notes.pop(msg.note)
                notes[idx] = Note(
                    midi_note=notes[idx].midi_note,
                    time=notes[idx].time,
                    duration=current_time - start_time
                )

    return sorted(notes, key=lambda n: n.time)


def get_tempo(mid: mido.MidiFile) -> int:
    """Get tempo from MIDI file, default to 120 BPM."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo
    return 500000  # Default: 120 BPM
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_parser.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/maestro/parser.py tests/test_parser.py
git commit -m "feat: add MIDI parser module"
```

---

## Task 3: Player Module (Playback Engine)

**Files:**
- Create: `src/maestro/player.py`
- Create: `tests/test_player.py`

**Step 1: Write the failing test**

Create `tests/test_player.py`:

```python
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
    """Create a simple test MIDI."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
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


def test_player_pause_changes_state(sample_midi, mock_keyboard):
    """Pausing should change state to PAUSED."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    player.pause()
    assert player.state == PlaybackState.PAUSED
    player.stop()


def test_player_stop_changes_state(sample_midi, mock_keyboard):
    """Stopping should change state to STOPPED."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    player.stop()
    assert player.state == PlaybackState.STOPPED
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_player.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write the implementation**

Create `src/maestro/player.py`:

```python
"""Playback engine for Maestro.

Handles playing MIDI notes via keyboard simulation.
"""

import threading
import time
from enum import Enum, auto
from pathlib import Path

from pynput.keyboard import Controller, Key

from maestro.keymap import midi_note_to_key
from maestro.parser import parse_midi, Note


class PlaybackState(Enum):
    """Player state machine states."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class Player:
    """MIDI playback engine with keyboard simulation."""

    MIN_NOTE_DELAY = 0.05  # Minimum 50ms between keypresses

    def __init__(self):
        self.keyboard = Controller()
        self.state = PlaybackState.STOPPED
        self.current_song: Path | None = None
        self._notes: list[Note] = []
        self._playback_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._note_index = 0
        self._pause_time: float = 0.0

    def load(self, midi_path: Path) -> None:
        """Load a MIDI file for playback."""
        self._notes = parse_midi(midi_path)
        self.current_song = midi_path
        self._note_index = 0

    def play(self) -> None:
        """Start or resume playback."""
        if self.state == PlaybackState.PLAYING:
            return

        if self.state == PlaybackState.PAUSED:
            # Resume from pause
            self._pause_event.set()
            self.state = PlaybackState.PLAYING
            return

        if not self._notes:
            return

        # Start fresh playback
        self._stop_event.clear()
        self._pause_event.clear()
        self._note_index = 0
        self.state = PlaybackState.PLAYING

        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def pause(self) -> None:
        """Pause playback."""
        if self.state == PlaybackState.PLAYING:
            self._pause_event.clear()
            self.state = PlaybackState.PAUSED

    def stop(self) -> None:
        """Stop playback completely."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        self.state = PlaybackState.STOPPED
        self._note_index = 0

        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)

    def toggle_pause(self) -> None:
        """Toggle between playing and paused."""
        if self.state == PlaybackState.PLAYING:
            self.pause()
        elif self.state == PlaybackState.PAUSED:
            self.play()

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread."""
        start_time = time.time()

        while self._note_index < len(self._notes):
            if self._stop_event.is_set():
                break

            # Handle pause
            if self.state == PlaybackState.PAUSED:
                pause_start = time.time()
                self._pause_event.wait()  # Block until unpaused
                if self._stop_event.is_set():
                    break
                # Adjust start time to account for pause duration
                start_time += time.time() - pause_start

            note = self._notes[self._note_index]
            current_time = time.time() - start_time

            # Wait until it's time to play this note
            if note.time > current_time:
                sleep_time = note.time - current_time
                # Sleep in small increments to stay responsive
                while sleep_time > 0 and not self._stop_event.is_set():
                    time.sleep(min(0.01, sleep_time))
                    sleep_time = note.time - (time.time() - start_time)
                    if self.state == PlaybackState.PAUSED:
                        break

                if self._stop_event.is_set() or self.state == PlaybackState.PAUSED:
                    continue

            # Play the note
            key = midi_note_to_key(note.midi_note)
            self._press_key(key)

            self._note_index += 1

        # Playback finished
        if not self._stop_event.is_set():
            self.state = PlaybackState.STOPPED

    def _press_key(self, key: str) -> None:
        """Simulate a keypress."""
        try:
            self.keyboard.press(key)
            time.sleep(0.02)  # Brief hold
            self.keyboard.release(key)
        except Exception:
            pass  # Ignore key errors
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_player.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/maestro/player.py tests/test_player.py
git commit -m "feat: add player module with playback engine"
```

---

## Task 4: GUI Module (Song Picker)

**Files:**
- Create: `src/maestro/gui.py`
- Create: `tests/test_gui.py`

**Step 1: Write the failing test**

Create `tests/test_gui.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from maestro.gui import SongPicker, get_songs_from_folder


@pytest.fixture
def songs_folder(tmp_path):
    """Create a folder with test MIDI files."""
    (tmp_path / "song1.mid").touch()
    (tmp_path / "song2.mid").touch()
    (tmp_path / "not_midi.txt").touch()
    return tmp_path


def test_get_songs_from_folder(songs_folder):
    """Should return only .mid files."""
    songs = get_songs_from_folder(songs_folder)
    assert len(songs) == 2
    assert all(s.suffix == ".mid" for s in songs)


def test_get_songs_from_empty_folder(tmp_path):
    """Empty folder returns empty list."""
    songs = get_songs_from_folder(tmp_path)
    assert songs == []


def test_get_songs_from_nonexistent_folder():
    """Nonexistent folder returns empty list."""
    songs = get_songs_from_folder(Path("/nonexistent"))
    assert songs == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_gui.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write the implementation**

Create `src/maestro/gui.py`:

```python
"""Tkinter GUI for song selection.

Provides a simple window to browse and select MIDI files.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable


def get_songs_from_folder(folder: Path) -> list[Path]:
    """Get all MIDI files from a folder.

    Args:
        folder: Path to the songs folder

    Returns:
        List of paths to .mid files, sorted alphabetically
    """
    if not folder.exists():
        return []

    return sorted(folder.glob("*.mid"))


class SongPicker:
    """GUI window for selecting songs."""

    def __init__(
        self,
        songs_folder: Path,
        on_play: Callable[[Path], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        get_state: Callable[[], str],
    ):
        """Initialize the song picker.

        Args:
            songs_folder: Path to folder containing MIDI files
            on_play: Callback when play is clicked with selected song path
            on_pause: Callback when pause is clicked
            on_stop: Callback when stop is clicked
            get_state: Callback to get current playback state string
        """
        self.songs_folder = songs_folder
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.get_state = get_state

        self.window: tk.Tk | None = None
        self.song_listbox: tk.Listbox | None = None
        self.status_label: tk.Label | None = None
        self._songs: list[Path] = []

    def show(self) -> None:
        """Show the song picker window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            self._refresh_songs()
            return

        self.window = tk.Tk()
        self.window.title("Maestro - Song Picker")
        self.window.geometry("350x450")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Song list
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(list_frame, text="Songs:").pack(anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.song_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.song_listbox.pack(fill=tk.BOTH, expand=True)
        self.song_listbox.bind("<Double-1>", self._on_double_click)
        scrollbar.config(command=self.song_listbox.yview)

        # Control buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Play", command=self._on_play_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Pause", command=self._on_pause_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Stop", command=self._on_stop_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_songs).pack(side=tk.RIGHT, padx=2)

        # Status
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Stopped")
        self.status_label.pack(anchor=tk.W)

        self._refresh_songs()
        self._update_status()

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        if self.song_listbox is None:
            return

        self._songs = get_songs_from_folder(self.songs_folder)
        self.song_listbox.delete(0, tk.END)

        for song in self._songs:
            self.song_listbox.insert(tk.END, song.stem)

    def _get_selected_song(self) -> Path | None:
        """Get the currently selected song path."""
        if self.song_listbox is None:
            return None

        selection = self.song_listbox.curselection()
        if not selection:
            return None
        return self._songs[selection[0]]

    def _on_play_click(self) -> None:
        """Handle play button click."""
        song = self._get_selected_song()
        if song:
            self.on_play(song)
            self._update_status()

    def _on_pause_click(self) -> None:
        """Handle pause button click."""
        self.on_pause()
        self._update_status()

    def _on_stop_click(self) -> None:
        """Handle stop button click."""
        self.on_stop()
        self._update_status()

    def _on_double_click(self, event) -> None:
        """Handle double-click on song."""
        self._on_play_click()

    def _update_status(self) -> None:
        """Update the status label."""
        if self.status_label:
            state = self.get_state()
            self.status_label.config(text=f"Status: {state}")

    def _on_close(self) -> None:
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None
            self.song_listbox = None
            self.status_label = None

    def run(self) -> None:
        """Run the Tkinter main loop (blocking)."""
        if self.window:
            self.window.mainloop()

    def close(self) -> None:
        """Close the window."""
        self._on_close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_gui.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/maestro/gui.py tests/test_gui.py
git commit -m "feat: add GUI module with song picker"
```

---

## Task 5: Main Entry Point with Hotkeys

**Files:**
- Modify: `src/maestro/__init__.py`
- Create: `src/maestro/main.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

Create `tests/test_main.py`:

```python
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


def test_maestro_toggle_pause(mock_dependencies, tmp_path):
    """Toggle pause should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.toggle_pause()
    mock_dependencies['player'].toggle_pause.assert_called_once()


def test_maestro_stop(mock_dependencies, tmp_path):
    """Stop should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.stop()
    mock_dependencies['player'].stop.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write the implementation**

Create `src/maestro/main.py`:

```python
"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import sys
import threading
import time
from pathlib import Path

from pynput import keyboard

from maestro.player import Player, PlaybackState
from maestro.gui import SongPicker


class Maestro:
    """Main application coordinator."""

    SONGS_FOLDER = Path("songs")
    STARTUP_DELAY = 3.0  # Seconds before playback starts

    def __init__(self, songs_folder: Path | None = None):
        """Initialize Maestro.

        Args:
            songs_folder: Path to folder containing MIDI files.
                         Defaults to ./songs
        """
        self.songs_folder = songs_folder or self.SONGS_FOLDER
        self.songs_folder.mkdir(exist_ok=True)

        self.player = Player()
        self.picker = SongPicker(
            songs_folder=self.songs_folder,
            on_play=self._on_play,
            on_pause=self.toggle_pause,
            on_stop=self.stop,
            get_state=self._get_state_string,
        )

        self._hotkey_listener: keyboard.GlobalHotKeys | None = None
        self._gui_thread: threading.Thread | None = None

    def _on_play(self, song_path: Path) -> None:
        """Handle play request from GUI."""
        self.player.stop()
        self.player.load(song_path)

        # Start playback after delay (so user can switch to game)
        def delayed_play():
            print(f"Playing '{song_path.stem}' in {self.STARTUP_DELAY} seconds...")
            time.sleep(self.STARTUP_DELAY)
            if self.player.state == PlaybackState.STOPPED:
                self.player.play()

        threading.Thread(target=delayed_play, daemon=True).start()

    def _get_state_string(self) -> str:
        """Get current playback state as string."""
        return self.player.state.name.capitalize()

    def show_picker(self) -> None:
        """Show the song picker GUI."""
        if self._gui_thread is None or not self._gui_thread.is_alive():
            self._gui_thread = threading.Thread(target=self._run_gui, daemon=True)
            self._gui_thread.start()
        else:
            # GUI already running, just show it
            self.picker.show()

    def _run_gui(self) -> None:
        """Run the GUI in a separate thread."""
        self.picker.show()
        self.picker.run()

    def toggle_pause(self) -> None:
        """Toggle play/pause."""
        self.player.toggle_pause()

    def stop(self) -> None:
        """Stop playback."""
        self.player.stop()

    def start(self) -> None:
        """Start the application with hotkey listening."""
        print("Maestro ready!")
        print("  Alt+N: Open song picker")
        print("  Alt+M: Play/Pause")
        print("  Escape: Stop playback")
        print("  Ctrl+C: Exit")
        print()

        # Set up global hotkeys
        hotkeys = {
            '<alt>+n': self.show_picker,
            '<alt>+m': self.toggle_pause,
        }

        self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
        self._hotkey_listener.start()

        # Also listen for Escape key
        def on_press(key):
            if key == keyboard.Key.esc:
                self.stop()

        with keyboard.Listener(on_press=on_press) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")
                self.stop()
                if self._hotkey_listener:
                    self._hotkey_listener.stop()


def main():
    """Entry point."""
    app = Maestro()
    app.start()


if __name__ == "__main__":
    main()
```

Update `src/maestro/__init__.py`:

```python
"""Maestro - Heartopia music player."""

from maestro.main import main

__all__ = ["main"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_main.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/maestro/__init__.py src/maestro/main.py tests/test_main.py
git commit -m "feat: add main entry point with hotkey support"
```

---

## Task 6: Integration Testing & Polish

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for the full Maestro workflow."""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, Mock
import mido

from maestro.main import Maestro
from maestro.player import PlaybackState


@pytest.fixture
def songs_folder(tmp_path):
    """Create a songs folder with a test MIDI."""
    folder = tmp_path / "songs"
    folder.mkdir()

    # Create a simple test song
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # C major scale
    for note in [60, 62, 64, 65, 67, 69, 71, 72]:
        track.append(mido.Message('note_on', note=note, velocity=64, time=0))
        track.append(mido.Message('note_off', note=note, velocity=64, time=120))

    mid.save(folder / "test_scale.mid")
    return folder


@pytest.fixture
def mock_keyboard():
    """Mock keyboard to avoid actual keypresses."""
    with patch('maestro.player.Controller') as mock:
        yield mock.return_value


def test_full_playback_workflow(songs_folder, mock_keyboard):
    """Test loading and playing a song."""
    app = Maestro(songs_folder=songs_folder)

    # Load and play
    song = songs_folder / "test_scale.mid"
    app.player.load(song)
    app.player.play()

    time.sleep(0.1)
    assert app.player.state == PlaybackState.PLAYING

    # Pause
    app.toggle_pause()
    assert app.player.state == PlaybackState.PAUSED

    # Resume
    app.toggle_pause()
    assert app.player.state == PlaybackState.PLAYING

    # Stop
    app.stop()
    assert app.player.state == PlaybackState.STOPPED


def test_song_discovery(songs_folder):
    """Test that songs are discovered from folder."""
    from maestro.gui import get_songs_from_folder

    songs = get_songs_from_folder(songs_folder)
    assert len(songs) == 1
    assert songs[0].name == "test_scale.mid"
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_integration.py -v`
Expected: All tests PASS

**Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## Task 7: Final Setup & Manual Test

**Step 1: Create pytest config**

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

**Step 2: Create tests __init__.py**

```bash
touch tests/__init__.py
```

**Step 3: Test the CLI**

Run: `uv run maestro`
Expected: App starts, shows hotkey instructions

**Step 4: Manual test checklist**

- [ ] `uv run maestro` starts without errors
- [ ] Alt+N opens the song picker window
- [ ] Songs from `songs/` folder appear in list
- [ ] Double-clicking a song starts countdown
- [ ] Alt+M pauses/resumes playback
- [ ] Escape stops playback
- [ ] Ctrl+C exits cleanly

**Step 5: Final commit**

```bash
git add pyproject.toml tests/__init__.py
git commit -m "chore: finalize project setup"
```

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|-----------|
| 1 | Key mapping module | 5 |
| 2 | MIDI parser module | 5 |
| 3 | Player module | 5 |
| 4 | GUI module | 5 |
| 5 | Main entry point | 5 |
| 6 | Integration tests | 4 |
| 7 | Final setup | 5 |

**Total: 7 tasks, ~34 steps**
