"""Playback engine for Maestro.

Handles playing MIDI notes via keyboard simulation.
"""

import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path

from pynput.keyboard import Controller, Key

from maestro.game_mode import GameMode

# pydirectinput is Windows-only (uses ctypes.windll)
# Import conditionally and provide fallback
if sys.platform == "win32":
    import pydirectinput
    pydirectinput.PAUSE = 0  # Disable default 0.1s delay
else:
    pydirectinput = None  # type: ignore
from maestro.keymap import midi_note_to_key
from maestro.keymap_wwm import midi_note_to_key_wwm
from maestro.logger import setup_logger
from maestro.parser import parse_midi, Note


class PlaybackState(Enum):
    """Player state machine states."""
    STOPPED = auto()
    PLAYING = auto()


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
        self._note_index = 0
        self._start_time: float = 0.0
        self._game_mode = GameMode.HEARTOPIA
        self._last_key: str = ""
        self._speed: float = 1.0  # 1.0 = normal, 0.5 = half speed, 2.0 = double
        self._logger = setup_logger()
        self._last_error: str = ""
        self._transpose: bool = False

    @property
    def game_mode(self) -> GameMode:
        return self._game_mode

    @game_mode.setter
    def game_mode(self, value: GameMode) -> None:
        self._game_mode = value

    @property
    def last_key(self) -> str:
        """Last key pressed (for visual feedback)."""
        return self._last_key

    @property
    def last_error(self) -> str:
        """Last error message."""
        return self._last_error

    @property
    def transpose(self) -> bool:
        """Whether to transpose out-of-range notes into playable range."""
        return self._transpose

    @transpose.setter
    def transpose(self, value: bool) -> None:
        self._transpose = value

    @property
    def speed(self) -> float:
        """Playback speed multiplier (1.0 = normal, 0.5 = half speed)."""
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        self._speed = max(0.25, min(1.5, value))  # Clamp between 0.25 and 1.5

    @property
    def duration(self) -> float:
        """Total duration of current song in seconds."""
        if not self._notes:
            return 0.0
        last_note = self._notes[-1]
        return last_note.time + last_note.duration

    @property
    def position(self) -> float:
        """Current playback position in seconds (in song time, not real time)."""
        if self.state == PlaybackState.STOPPED or not self._notes:
            return 0.0
        if self._start_time == 0:
            return 0.0
        # Scale by speed so position reflects song time, not real time
        return (time.time() - self._start_time) * self._speed

    def load(self, midi_path: Path) -> None:
        """Load a MIDI file for playback."""
        self._notes = parse_midi(midi_path)
        self.current_song = midi_path
        self._note_index = 0

    def play(self) -> None:
        """Start playback."""
        if self.state == PlaybackState.PLAYING:
            return

        if not self._notes:
            return

        # Start fresh playback
        self._stop_event.clear()
        self._note_index = 0
        self._start_time = time.time()
        self.state = PlaybackState.PLAYING

        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def stop(self) -> None:
        """Stop playback completely."""
        self._stop_event.set()
        self.state = PlaybackState.STOPPED
        self._note_index = 0
        self._start_time = 0.0

        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)

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

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread."""
        while self._note_index < len(self._notes):
            if self._stop_event.is_set():
                break

            note = self._notes[self._note_index]
            # Scale elapsed time by speed to get song position
            current_time = (time.time() - self._start_time) * self._speed

            # Wait until it's time to play this note
            if note.time > current_time:
                # Convert song time difference to real time for sleeping
                sleep_time = (note.time - current_time) / self._speed
                # Sleep in small increments to stay responsive
                while sleep_time > 0 and not self._stop_event.is_set():
                    time.sleep(min(0.01, sleep_time))
                    current_time = (time.time() - self._start_time) * self._speed
                    sleep_time = (note.time - current_time) / self._speed

                if self._stop_event.is_set():
                    continue

            # Play the note
            if self._game_mode == GameMode.WHERE_WINDS_MEET:
                result = midi_note_to_key_wwm(note.midi_note, transpose=self._transpose)
                if result is not None:
                    key, modifier = result
                    self._press_key(key, modifier)
            else:
                key = midi_note_to_key(note.midi_note, transpose=self._transpose)
                if key is not None:
                    self._press_key(key)

            self._note_index += 1

        # Playback finished
        if not self._stop_event.is_set():
            self.state = PlaybackState.STOPPED

    def _press_key(self, key: str, modifier: Key | None = None) -> None:
        """Simulate a keypress with optional modifier.

        Uses pydirectinput for WWM mode (DirectInput) and pynput for Heartopia.
        """
        # Update last key for visual feedback
        if modifier:
            self._last_key = f"Shift+{key.upper()}"
        else:
            self._last_key = key.upper()

        try:
            if self._game_mode == GameMode.WHERE_WINDS_MEET and pydirectinput is not None:
                # Use DirectInput for WWM (game requires it)
                if modifier:
                    pydirectinput.keyDown('shift')
                    time.sleep(0.01)
                pydirectinput.keyDown(key)
                time.sleep(0.05)
                pydirectinput.keyUp(key)
                if modifier:
                    time.sleep(0.01)
                    pydirectinput.keyUp('shift')
            else:
                # Use pynput for Heartopia (or as fallback on non-Windows)
                if modifier:
                    self.keyboard.press(modifier)
                    time.sleep(0.01)
                self.keyboard.press(key)
                time.sleep(0.05)
                self.keyboard.release(key)
                if modifier:
                    time.sleep(0.01)
                    self.keyboard.release(modifier)
        except Exception as e:
            self._logger.error(f"Key press failed for '{key}': {e}")
            self._last_error = f"Key simulation failed: {e}"
