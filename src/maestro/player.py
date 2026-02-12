"""Playback engine for Maestro.

Handles playing MIDI notes via keyboard simulation.
"""

import atexit
import sys
import threading
import time
from dataclasses import dataclass
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
from maestro.key_layout import KeyLayout
from maestro.keymap import midi_note_to_key
from maestro.keymap_15_double import midi_note_to_key_15_double
from maestro.keymap_15_triple import midi_note_to_key_15_triple
from maestro.keymap_drums import midi_note_to_key as midi_note_to_key_drums
from maestro.keymap_xylophone import midi_note_to_key as midi_note_to_key_xylophone
from maestro.keymap_wwm import midi_note_to_key_wwm
from maestro.logger import setup_logger
from maestro.parser import Note, parse_midi


class PlaybackState(Enum):
    """Player state machine states."""

    STOPPED = auto()
    PLAYING = auto()


@dataclass
class KeyEvent:
    """A scheduled key press or release event."""

    time: float  # Time in seconds from start of song
    action: str  # "down" or "up"
    key: str  # Key to press/release
    modifier: Key | None = None


class Player:
    """MIDI playback engine with keyboard simulation."""

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
        self._key_layout = KeyLayout.KEYS_22
        self._sharp_handling: str = "skip"
        self._held_keys: set[tuple[str, Key | None]] = set()
        self._events: list[KeyEvent] = []
        # Event caching to avoid rebuilding on replays
        self._cached_events: list[KeyEvent] | None = None
        self._cached_cache_key: str | None = None
        atexit.register(self._release_all_keys)

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
        if self._transpose != value:
            self._invalidate_cache()
        self._transpose = value

    @property
    def key_layout(self) -> KeyLayout:
        """Current key layout for Heartopia."""
        return self._key_layout

    @key_layout.setter
    def key_layout(self, value: KeyLayout) -> None:
        if self._key_layout != value:
            self._invalidate_cache()
        self._key_layout = value

    @property
    def sharp_handling(self) -> str:
        """How to handle sharp notes on 15-key layouts ('skip' or 'snap')."""
        return self._sharp_handling

    @sharp_handling.setter
    def sharp_handling(self, value: str) -> None:
        if value in ("skip", "snap"):
            if self._sharp_handling != value:
                self._invalidate_cache()
            self._sharp_handling = value

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
        # Invalidate cache if loading a different song
        if self.current_song != midi_path:
            self._invalidate_cache()
        self._notes = parse_midi(midi_path)
        self.current_song = midi_path
        self._note_index = 0

    def play(self) -> None:
        """Start playback."""
        if self.state == PlaybackState.PLAYING:
            return

        if not self._notes:
            return

        self._stop_event.clear()
        self._note_index = 0
        self._held_keys.clear()
        self._start_time = time.time()
        self.state = PlaybackState.PLAYING

        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def stop(self) -> None:
        """Stop playback completely."""
        self._stop_event.set()
        self._release_all_keys()
        self.state = PlaybackState.STOPPED
        self._note_index = 0
        self._start_time = 0.0
        self._events = []

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
        for note in self._notes[self._note_index :]:
            if note.time > end_pos:
                break
            if note.time >= current_pos:
                upcoming.append(note)

        return upcoming

    def _invalidate_cache(self) -> None:
        """Invalidate the event cache."""
        self._cached_events = None
        self._cached_cache_key = None

    def _get_cache_key(self) -> str:
        """Generate a cache key based on current state.

        Returns:
            String uniquely identifying the current song + settings combination.
        """
        song_path = str(self.current_song) if self.current_song else "none"
        return f"{song_path}|{self._game_mode.name}|{self._key_layout.name}|{self._transpose}|{self._sharp_handling}"

    def _resolve_key(self, midi_note: int) -> tuple[str, Key | None] | None:
        """Resolve a MIDI note to a key press based on current game mode and layout.

        Returns:
            Tuple of (key, modifier) or None if note can't be played
        """
        if self._game_mode == GameMode.WHERE_WINDS_MEET:
            result = midi_note_to_key_wwm(midi_note, transpose=self._transpose)
            if result is not None:
                return result  # Already returns (key, modifier)
            return None

        # Heartopia mode - dispatch based on key layout
        if self._key_layout == KeyLayout.KEYS_15_DOUBLE:
            key = midi_note_to_key_15_double(
                midi_note, transpose=self._transpose, sharp_handling=self._sharp_handling
            )
        elif self._key_layout == KeyLayout.KEYS_15_TRIPLE:
            key = midi_note_to_key_15_triple(
                midi_note, transpose=self._transpose, sharp_handling=self._sharp_handling
            )
        elif self._key_layout == KeyLayout.DRUMS:
            key = midi_note_to_key_drums(midi_note, transpose=False)  # Drums never transpose
        elif self._key_layout == KeyLayout.XYLOPHONE:
            key = midi_note_to_key_xylophone(midi_note, transpose=False)  # Xylophone never transposes
        else:  # KEYS_22
            key = midi_note_to_key(midi_note, transpose=self._transpose)

        if key is not None:
            return (key, None)
        return None

    def _build_events(self) -> list[KeyEvent]:
        """Convert notes to sorted key down/up events.

        Uses caching to avoid rebuilding events when replaying the same song
        with the same settings.

        Returns:
            List of KeyEvent objects sorted by time, with "up" events before "down"
            events at the same timestamp (to allow key re-press).
        """
        # Check if we can use cached events
        current_cache_key = self._get_cache_key()
        if self._cached_events is not None and self._cached_cache_key == current_cache_key:
            return self._cached_events

        # Build events from scratch
        events = []
        for note in self._notes:
            result = self._resolve_key(note.midi_note)
            if result is None:
                continue
            key, modifier = result

            events.append(
                KeyEvent(
                    time=note.time,
                    action="down",
                    key=key,
                    modifier=modifier,
                )
            )
            events.append(
                KeyEvent(
                    time=note.time + note.duration,
                    action="up",
                    key=key,
                    modifier=modifier,
                )
            )

        # Sort by time, then "up" before "down" at same time (allows re-press)
        events.sort(key=lambda e: (e.time, 0 if e.action == "up" else 1))

        # Cache the result
        self._cached_events = events
        self._cached_cache_key = current_cache_key

        return events

    def _key_down(self, key: str, modifier: Key | None = None) -> None:
        """Press a key down and track it."""
        key_id = (key, modifier)
        if key_id in self._held_keys:
            return  # Already held

        # Update last key for visual feedback
        if modifier:
            self._last_key = f"Shift+{key.upper()}"
        else:
            self._last_key = key.upper()

        try:
            if self._game_mode == GameMode.WHERE_WINDS_MEET and pydirectinput is not None:
                if modifier:
                    pydirectinput.keyDown("shift")
                    time.sleep(0.01)
                pydirectinput.keyDown(key)
            else:
                if modifier:
                    self.keyboard.press(modifier)
                    time.sleep(0.01)
                self.keyboard.press(key)
            self._held_keys.add(key_id)
        except Exception as e:
            self._logger.error(f"Key down failed for '{key}': {e}")
            self._last_error = f"Key simulation failed: {e}"

    def _key_up(self, key: str, modifier: Key | None = None) -> None:
        """Release a key."""
        key_id = (key, modifier)
        if key_id not in self._held_keys:
            return  # Not held

        try:
            if self._game_mode == GameMode.WHERE_WINDS_MEET and pydirectinput is not None:
                pydirectinput.keyUp(key)
                if modifier:
                    # Only release shift if no other shift keys are held
                    shift_keys = [
                        (k, m) for k, m in self._held_keys if m is not None and (k, m) != key_id
                    ]
                    if not shift_keys:
                        pydirectinput.keyUp("shift")
            else:
                self.keyboard.release(key)
                if modifier:
                    shift_keys = [
                        (k, m) for k, m in self._held_keys if m is not None and (k, m) != key_id
                    ]
                    if not shift_keys:
                        self.keyboard.release(modifier)
            self._held_keys.discard(key_id)
        except Exception as e:
            self._logger.error(f"Key up failed for '{key}': {e}")

    def _release_all_keys(self) -> None:
        """Release all currently held keys (safety cleanup)."""
        for key, modifier in list(self._held_keys):
            try:
                if self._game_mode == GameMode.WHERE_WINDS_MEET and pydirectinput is not None:
                    pydirectinput.keyUp(key)
                    if modifier:
                        pydirectinput.keyUp("shift")
                else:
                    self.keyboard.release(key)
                    if modifier:
                        self.keyboard.release(modifier)
            except Exception:
                pass
        self._held_keys.clear()

    def _is_game_window_active(self) -> bool:
        """Check if the game window is currently in focus.

        On Windows, uses win32gui to check the foreground window title.
        On non-Windows platforms, always returns True (no detection available).
        """
        if sys.platform != "win32":
            return True

        try:
            import win32gui

            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).lower()

            if self._game_mode == GameMode.HEARTOPIA:
                return "heartopia" in title
            elif self._game_mode == GameMode.WHERE_WINDS_MEET:
                return "where winds meet" in title
            return True
        except Exception:
            return True  # If detection fails, don't block playback

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread.

        Uses event-driven approach: each note becomes a key-down and key-up event.
        Events at the same timestamp are processed simultaneously (chords).
        Automatically pauses when the game window loses focus.
        """
        self._events = self._build_events()
        event_index = 0

        while event_index < len(self._events):
            if self._stop_event.is_set():
                break

            # Check window focus - pause if game not in foreground
            if not self._is_game_window_active():
                pause_start = time.time()
                while not self._is_game_window_active() and not self._stop_event.is_set():
                    time.sleep(0.1)  # Check every 100ms
                if self._stop_event.is_set():
                    break
                # Adjust start time to account for pause duration
                self._start_time += time.time() - pause_start

            event = self._events[event_index]
            # Scale elapsed time by speed to get song position
            current_time = (time.time() - self._start_time) * self._speed

            # Wait until it's time for this event
            if event.time > current_time:
                sleep_time = (event.time - current_time) / self._speed
                while sleep_time > 0 and not self._stop_event.is_set():
                    time.sleep(min(0.005, sleep_time))
                    current_time = (time.time() - self._start_time) * self._speed
                    sleep_time = (event.time - current_time) / self._speed

                if self._stop_event.is_set():
                    break

            # Process this event and all events at the same timestamp
            current_event_time = event.time
            while (
                event_index < len(self._events)
                and self._events[event_index].time <= current_event_time + 0.001
            ):
                evt = self._events[event_index]
                if evt.action == "down":
                    self._key_down(evt.key, evt.modifier)
                else:
                    self._key_up(evt.key, evt.modifier)
                event_index += 1

        # Clean up: release all held keys
        self._release_all_keys()

        # Playback finished
        if not self._stop_event.is_set():
            self.state = PlaybackState.STOPPED
