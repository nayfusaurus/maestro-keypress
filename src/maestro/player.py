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
