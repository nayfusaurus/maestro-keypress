"""Background worker threads for MIDI validation and update checking."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from maestro.key_layout import KeyLayout, WwmLayout
from maestro.parser import get_midi_info, parse_midi
from maestro.update_checker import check_for_updates


class ValidationWorker(QThread):
    """Background thread that validates MIDI files.

    Emits song_validated for each file processed, and validation_finished when done.
    Uses mtime caching to skip unchanged files. Computes note compatibility inline.
    """

    song_validated = Signal(
        str, str, dict, list, int, int
    )  # path_str, status, info, notes, playable, total
    validation_finished = Signal()

    def __init__(
        self,
        songs: list[Path],
        key_layout: KeyLayout,
        game_mode: str,
        transpose: bool,
        sharp_handling: str,
        validation_cache: dict[str, tuple[float, bool]],
        song_info: dict[str, dict],
        song_notes: dict[str, list],
        wwm_layout: WwmLayout = WwmLayout.KEYS_36,
    ) -> None:
        super().__init__()
        self._songs = list(songs)
        self._key_layout = key_layout
        self._wwm_layout = wwm_layout
        self._game_mode = game_mode
        self._transpose = transpose
        self._sharp_handling = sharp_handling
        self._validation_cache = validation_cache
        self._song_info = song_info
        self._song_notes = song_notes

    def _compute_compatibility(self, notes: list) -> tuple[int, int]:
        """Calculate how many notes are playable with current layout."""
        from maestro.game_mode import GameMode
        from maestro.keymap import midi_note_to_key
        from maestro.keymap_15_double import midi_note_to_key_15_double
        from maestro.keymap_15_triple import midi_note_to_key_15_triple
        from maestro.keymap_drums import midi_note_to_key as midi_note_to_key_drums
        from maestro.keymap_once_human import midi_note_to_key_once_human
        from maestro.keymap_wwm import midi_note_to_key_wwm, midi_note_to_key_wwm_21
        from maestro.keymap_xylophone import midi_note_to_key as midi_note_to_key_xylophone

        total = len(notes)
        if total == 0:
            return (0, 0)

        playable = 0
        for note in notes:
            midi = note.midi_note
            result: object = None
            if self._game_mode == GameMode.WHERE_WINDS_MEET.value:
                if self._wwm_layout == WwmLayout.KEYS_21:
                    result = midi_note_to_key_wwm_21(
                        midi,
                        transpose=self._transpose,
                        sharp_handling=self._sharp_handling,
                    )
                else:
                    result = midi_note_to_key_wwm(midi, transpose=self._transpose)
            elif self._game_mode == GameMode.ONCE_HUMAN.value:
                result = midi_note_to_key_once_human(midi, transpose=self._transpose)
            elif self._key_layout == KeyLayout.KEYS_15_DOUBLE:
                result = midi_note_to_key_15_double(
                    midi, transpose=self._transpose, sharp_handling=self._sharp_handling
                )
            elif self._key_layout == KeyLayout.KEYS_15_TRIPLE:
                result = midi_note_to_key_15_triple(
                    midi, transpose=self._transpose, sharp_handling=self._sharp_handling
                )
            elif self._key_layout == KeyLayout.DRUMS:
                result = midi_note_to_key_drums(midi, transpose=False)
            elif self._key_layout == KeyLayout.XYLOPHONE:
                result = midi_note_to_key_xylophone(midi, transpose=False)
            else:
                result = midi_note_to_key(midi, transpose=self._transpose)
            if result is not None:
                playable += 1

        return (playable, total)

    def run(self) -> None:
        """Validate all songs, emitting results as signals."""
        empty_info: dict = {"duration": 0, "bpm": 0, "note_count": 0}

        for song in self._songs:
            if self.isInterruptionRequested():
                return
            song_str = str(song)

            # Check if file still exists
            if not song.exists():
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [], 0, 0)
                continue

            # Get current mtime
            try:
                current_mtime = song.stat().st_mtime
            except OSError:
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [], 0, 0)
                continue

            # Check cache
            cached_entry = self._validation_cache.get(song_str)
            if cached_entry is not None:
                cached_mtime, cached_is_valid = cached_entry
                if cached_mtime == current_mtime:
                    if cached_is_valid:
                        # Reuse existing info/notes from the shared dicts
                        info = self._song_info.get(song_str, empty_info.copy())
                        notes = self._song_notes.get(song_str, [])
                        try:
                            playable, total = self._compute_compatibility(notes)
                        except Exception:
                            playable, total = 0, 0
                        self.song_validated.emit(song_str, "valid", info, notes, playable, total)
                    else:
                        self.song_validated.emit(song_str, "invalid", empty_info.copy(), [], 0, 0)
                    continue

            # File changed or not in cache — validate it
            try:
                notes = parse_midi(song)
                info = get_midi_info(song, notes=notes)

                # For drums layout, check if song has notes in drum range (60-67)
                if self._key_layout == KeyLayout.DRUMS:
                    has_drum_notes = any(60 <= note.midi_note <= 67 for note in notes)
                    if not has_drum_notes:
                        self._validation_cache[song_str] = (current_mtime, False)
                        self.song_validated.emit(song_str, "invalid", empty_info.copy(), [], 0, 0)
                        continue

                self._validation_cache[song_str] = (current_mtime, True)
                try:
                    playable, total = self._compute_compatibility(notes)
                except Exception:
                    playable, total = 0, 0
                self.song_validated.emit(song_str, "valid", info, notes, playable, total)
            except Exception:
                self._validation_cache[song_str] = (current_mtime, False)
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [], 0, 0)

        self.validation_finished.emit()


class UpdateCheckWorker(QThread):
    """Background thread that checks GitHub for new releases."""

    update_result = Signal(object)  # UpdateInfo namedtuple

    def __init__(self, current_version: str, repo: str, timeout: int = 5) -> None:
        super().__init__()
        self._current_version = current_version
        self._repo = repo
        self._timeout = timeout

    def run(self) -> None:
        """Check for updates and emit the result."""
        result = check_for_updates(self._current_version, self._repo, self._timeout)
        self.update_result.emit(result)
