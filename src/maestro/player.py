"""Playback engine for Maestro.

Handles playing MIDI notes via keyboard simulation.
"""

import atexit
import gc
import json
import sys
import threading
import time
from dataclasses import dataclass, replace
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
    pydirectinput = None
from maestro.key_layout import KeyLayout, WwmLayout
from maestro.keymap import midi_note_to_key
from maestro.keymap_15_double import midi_note_to_key_15_double
from maestro.keymap_15_triple import midi_note_to_key_15_triple
from maestro.keymap_drums import midi_note_to_key as midi_note_to_key_drums
from maestro.keymap_once_human import midi_note_to_key_once_human
from maestro.keymap_wwm import midi_note_to_key_wwm, midi_note_to_key_wwm_21
from maestro.keymap_xylophone import midi_note_to_key as midi_note_to_key_xylophone
from maestro.logger import setup_logger
from maestro.parser import Note, notes_duration, parse_midi

# Game modes that require DirectInput (pydirectinput) instead of pynput
_DIRECTINPUT_MODES = frozenset({GameMode.WHERE_WINDS_MEET, GameMode.ONCE_HUMAN})

# Fixed silence tail added after the last note so songs never end abruptly.
# Matches the minimum and maximum — i.e. always exactly this much.
TAIL_SILENCE_SECONDS = 2.0


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
    midi_note: int = 0  # Effective MIDI note after transpose/snap


class Player:
    """MIDI playback engine with keyboard simulation."""

    def __init__(self):
        self.keyboard = Controller()
        self.state = PlaybackState.STOPPED
        self.current_song: Path | None = None
        self._notes: list[Note] = []
        self._playback_thread: threading.Thread | None = None
        self._duration = 0.0
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
        self._wwm_layout = WwmLayout.KEYS_36
        self._sharp_handling: str = "skip"
        self._held_keys: set[tuple[str, Key | None]] = set()
        self._held_keys_lock = threading.Lock()
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
    def wwm_layout(self) -> WwmLayout:
        """Current key layout for Where Winds Meet."""
        return self._wwm_layout

    @wwm_layout.setter
    def wwm_layout(self, value: WwmLayout) -> None:
        if self._wwm_layout != value:
            self._invalidate_cache()
        self._wwm_layout = value

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
        new_speed = max(0.5, min(2.0, value))  # Clamp to match GUI slider range
        if self.state == PlaybackState.PLAYING and self._start_time:
            # Re-anchor start_time so the current song position stays continuous
            now = time.time()
            elapsed_song_time = (now - self._start_time) * self._speed
            self._start_time = now - elapsed_song_time / new_speed
        self._speed = new_speed

    @property
    def duration(self) -> float:
        """Total duration of current song in seconds, including a fixed
        trailing-silence tail so songs never end abruptly."""
        return self._duration

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
        self._duration = notes_duration(self._notes) + TAIL_SILENCE_SECONDS if self._notes else 0.0
        self._note_index = 0

    def play(self) -> None:
        """Start playback."""
        if self.state == PlaybackState.PLAYING:
            return

        if not self._notes:
            return

        self._stop_event.clear()
        self._note_index = 0
        with self._held_keys_lock:
            self._held_keys.clear()

        # Flush any pending garbage cycles, then disable the cyclic GC for the
        # duration of playback. Reference counting still frees objects normally;
        # this only suppresses periodic generational sweeps that could pause
        # the playback thread for tens of ms and disturb screen recorders.
        gc.collect()
        gc.disable()

        self._start_time = time.time()
        self.state = PlaybackState.PLAYING

        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def stop(self) -> None:
        """Stop playback completely."""
        self._stop_event.set()
        self._release_all_keys()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()
        self.state = PlaybackState.STOPPED
        self._note_index = 0
        self._start_time = 0.0

        # Re-enable cyclic GC after playback ends. Idempotent if already enabled.
        gc.enable()

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

        Includes the file mtime so that a MIDI file replaced on disk at the
        same path (delete + re-save) produces a different key and forces a
        rebuild — otherwise the user would hear the previous file's events.

        Returns:
            String uniquely identifying the current song + settings combination.
        """
        if self.current_song is None:
            song_key = "none"
        else:
            try:
                mtime = self.current_song.stat().st_mtime
            except OSError:
                mtime = 0.0
            song_key = f"{self.current_song}@{mtime}"
        return f"{song_key}|{self._game_mode.name}|{self._key_layout.name}|{self._wwm_layout.name}|{self._transpose}|{self._sharp_handling}"

    def _resolve_key(self, midi_note: int) -> tuple[str, int, Key | None] | None:
        """Resolve a MIDI note to a key press based on current game mode and layout.

        Returns:
            Tuple of (key, effective_midi_note, modifier) or None if note can't be played
        """
        if self._game_mode == GameMode.WHERE_WINDS_MEET:
            if self._wwm_layout == WwmLayout.KEYS_21:
                return midi_note_to_key_wwm_21(
                    midi_note, transpose=self._transpose, sharp_handling=self._sharp_handling
                )
            return midi_note_to_key_wwm(midi_note, transpose=self._transpose)

        if self._game_mode == GameMode.ONCE_HUMAN:
            return midi_note_to_key_once_human(midi_note, transpose=self._transpose)

        # Heartopia mode - dispatch based on key layout
        if self._key_layout == KeyLayout.KEYS_15_DOUBLE:
            result = midi_note_to_key_15_double(
                midi_note, transpose=self._transpose, sharp_handling=self._sharp_handling
            )
        elif self._key_layout == KeyLayout.KEYS_15_TRIPLE:
            result = midi_note_to_key_15_triple(
                midi_note, transpose=self._transpose, sharp_handling=self._sharp_handling
            )
        elif self._key_layout == KeyLayout.DRUMS:
            result = midi_note_to_key_drums(midi_note, transpose=False)  # Drums never transpose
        elif self._key_layout == KeyLayout.XYLOPHONE:
            result = midi_note_to_key_xylophone(
                midi_note, transpose=False
            )  # Xylophone never transposes
        else:  # KEYS_22
            result = midi_note_to_key(midi_note, transpose=self._transpose)

        if result is not None:
            key_char, effective_note = result
            return (key_char, effective_note, None)
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
            key, effective_note, modifier = result

            events.append(
                KeyEvent(
                    time=note.time,
                    action="down",
                    key=key,
                    modifier=modifier,
                    midi_note=effective_note,
                )
            )
            events.append(
                KeyEvent(
                    time=note.time + note.duration,
                    action="up",
                    key=key,
                    modifier=modifier,
                    midi_note=effective_note,
                )
            )

        # Sort by time, then "up" before "down" at same time (allows re-press)
        events.sort(key=lambda e: (e.time, 0 if e.action == "up" else 1))

        # Cache the result
        self._cached_events = events
        self._cached_cache_key = current_cache_key

        return events

    @staticmethod
    def _modifier_name(modifier: Key) -> str:
        """Return display/pydirectinput name for a modifier key."""
        if modifier == Key.shift:
            return "shift"
        return "ctrl"

    def _key_down(self, key: str, modifier: Key | None = None) -> bool:
        """Press a key down and track it."""
        key_id = (key, modifier)
        with self._held_keys_lock:
            if key_id in self._held_keys:
                return False  # Already held
            self._held_keys.add(key_id)

        # Update last key for visual feedback
        if modifier:
            self._last_key = f"{self._modifier_name(modifier).title()}+{key.upper()}"
        else:
            self._last_key = key.upper()

        try:
            if self._game_mode in _DIRECTINPUT_MODES and pydirectinput is not None:
                if modifier:
                    pydirectinput.keyDown(self._modifier_name(modifier))
                    time.sleep(0.01)
                pydirectinput.keyDown(key)
            else:
                if modifier:
                    self.keyboard.press(modifier)
                    time.sleep(0.01)
                self.keyboard.press(key)
        except Exception as e:
            return True
            with self._held_keys_lock:
                self._held_keys.discard(key_id)
            self._logger.error(f"Key down failed for '{key}': {e}")
            self._last_error = f"Key simulation failed: {e}"

            return False
    def _key_up(self, key: str, modifier: Key | None = None) -> bool:
        """Release a key."""
        key_id = (key, modifier)
        with self._held_keys_lock:
            if key_id not in self._held_keys:
                return False  # Not held
            self._held_keys.discard(key_id)
            # Check if any other keys still use this modifier
            release_modifier = modifier is not None and not any(
                m == modifier for _, m in self._held_keys
            )

        try:
            if self._game_mode in _DIRECTINPUT_MODES and pydirectinput is not None:
                pydirectinput.keyUp(key)
                if release_modifier:
                    pydirectinput.keyUp(self._modifier_name(modifier))
            else:
                self.keyboard.release(key)
                if release_modifier:
                    self.keyboard.release(modifier)
        except Exception as e:
            return True
            self._logger.error(f"Key up failed for '{key}': {e}")

            return False
    def _release_all_keys(self) -> None:
        """Release all currently held keys (safety cleanup)."""
        with self._held_keys_lock:
            held = list(self._held_keys)
            self._held_keys.clear()

        # Collect unique modifiers to release once each
        modifiers_to_release: set[Key] = set()
        for key, modifier in held:
            try:
                if self._game_mode in _DIRECTINPUT_MODES and pydirectinput is not None:
                    pydirectinput.keyUp(key)
                else:
                    self.keyboard.release(key)
            except Exception:  # nosec B110
                pass
            if modifier:
                modifiers_to_release.add(modifier)

        for modifier in modifiers_to_release:
            try:
                if self._game_mode in _DIRECTINPUT_MODES and pydirectinput is not None:
                    pydirectinput.keyUp(self._modifier_name(modifier))
                else:
                    self.keyboard.release(modifier)
            except Exception:  # nosec B110
                pass

    def _export_played_notes(self, played: list[KeyEvent], elapsed: float) -> None:
        """Export played notes to a .played.json file next to the MIDI."""
        if not self.current_song:
            return

        json_path = self.current_song.with_suffix(".played.json")

        # Match releases to the physical key and modifier that were pressed.
        pending: dict[tuple[str, Key | None], KeyEvent] = {}
        notes = []

        for evt in played:
            pair_key = (evt.key, evt.modifier)
            if evt.action == "down":
                pending[pair_key] = evt
            elif evt.action == "up" and pair_key in pending:
                start = pending.pop(pair_key)
                notes.append(
                    {
                        "midi_note": start.midi_note,
                        "start_sec": round(start.time, 6),
                        "end_sec": round(evt.time, 6),
                    }
                )

        # Close any still-pending notes (interrupted playback)
        for start in pending.values():
            notes.append(
                {
                    "midi_note": start.midi_note,
                    "start_sec": round(start.time, 6),
                    "end_sec": round(elapsed, 6),
                }
            )

        notes.sort(key=lambda n: n["start_sec"])

        data = {
            "source_midi": self.current_song.name,
            "speed": self._speed,
            "transpose": self._transpose,
            "sharp_handling": self._sharp_handling,
            "layout": self._key_layout.name,
            "events": notes,
        }

        try:
            from maestro.stats import update_stats

            if played:
                update_stats(played, self.current_song.name, elapsed, self._game_mode.value)
        except Exception:
            pass

        try:
            json_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self._logger.error(f"Failed to export played notes: {e}")

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

            return self._game_mode.value.lower() in title
        except Exception:
            return False

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread.

        Uses event-driven approach: each note becomes a key-down and key-up event.
        Events at the same timestamp are processed simultaneously (chords).
        Automatically pauses when the game window loses focus.
        """
        played: list[KeyEvent] = []
        active_start = time.monotonic()
        event_index = 0

        try:
            events = self._build_events()
            while event_index < len(events) and not self._stop_event.is_set():
                if not self._is_game_window_active():
                    pause_start = time.monotonic()
                    while not self._stop_event.wait(0.1) and not self._is_game_window_active():
                        pass
                    paused = time.monotonic() - pause_start
                    self._start_time += paused
                    active_start += paused
                    continue

                event_time = events[event_index].time
                delay = (event_time - self.position) / self._speed
                if delay > 0:
                    # Returning to the focus check after every wait also catches
                    # window changes during rests before the next chord is sent.
                    self._stop_event.wait(min(delay, 0.1))
                    continue

                while event_index < len(events) and events[event_index].time <= event_time + 0.001:
                    if self._stop_event.is_set():
                        break
                    evt = events[event_index]
                    dispatch = self._key_down if evt.action == "down" else self._key_up
                    if dispatch(evt.key, evt.modifier):
                        played.append(replace(evt, time=time.monotonic() - active_start))
                    event_index += 1
        finally:
            self._release_all_keys()
            elapsed = time.monotonic() - active_start
            try:
                self._export_played_notes(played, elapsed)
                if not self._stop_event.is_set():
                    self._stop_event.wait(timeout=TAIL_SILENCE_SECONDS / self._speed)
            finally:
                gc.enable()
                self.state = PlaybackState.STOPPED
