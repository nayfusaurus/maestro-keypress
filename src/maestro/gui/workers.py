"""Background worker threads for MIDI validation and update checking."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from maestro.key_layout import KeyLayout
from maestro.parser import get_midi_info, parse_midi
from maestro.update_checker import check_for_updates


class ValidationWorker(QThread):
    """Background thread that validates MIDI files.

    Emits song_validated for each file processed, and validation_finished when done.
    Uses mtime caching to skip unchanged files.
    """

    song_validated = Signal(str, str, dict, list)  # path_str, status, info_dict, notes_list
    validation_finished = Signal()

    def __init__(
        self,
        songs: list[Path],
        key_layout: KeyLayout,
        validation_cache: dict[str, tuple[float, bool]],
        song_info: dict[str, dict],
        song_notes: dict[str, list],
    ) -> None:
        super().__init__()
        self._songs = list(songs)
        self._key_layout = key_layout
        self._validation_cache = validation_cache
        self._song_info = song_info
        self._song_notes = song_notes

    def run(self) -> None:
        """Validate all songs, emitting results as signals."""
        empty_info: dict = {"duration": 0, "bpm": 0, "note_count": 0}

        for song in self._songs:
            song_str = str(song)

            # Check if file still exists
            if not song.exists():
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [])
                continue

            # Get current mtime
            try:
                current_mtime = song.stat().st_mtime
            except OSError:
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [])
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
                        self.song_validated.emit(song_str, "valid", info, notes)
                    else:
                        self.song_validated.emit(song_str, "invalid", empty_info.copy(), [])
                    continue

            # File changed or not in cache — validate it
            try:
                info = get_midi_info(song)
                notes = parse_midi(song)

                # For drums layout, check if song has notes in drum range (60-67)
                if self._key_layout == KeyLayout.DRUMS:
                    has_drum_notes = any(60 <= note.midi_note <= 67 for note in notes)
                    if not has_drum_notes:
                        self._validation_cache[song_str] = (current_mtime, False)
                        self.song_validated.emit(song_str, "invalid", empty_info.copy(), [])
                        continue

                self._validation_cache[song_str] = (current_mtime, True)
                self.song_validated.emit(song_str, "valid", info, notes)
            except Exception:
                self._validation_cache[song_str] = (current_mtime, False)
                self.song_validated.emit(song_str, "invalid", empty_info.copy(), [])

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


class ImportWorker(QThread):
    """Background thread that handles URL import (OnlineSequencer or YouTube).

    Detects the URL type, runs the appropriate pipeline, and emits signals
    for progress, completion, and errors.
    """

    progress = Signal(str)  # Progress status text
    finished = Signal(str)  # Filename of imported MIDI
    error = Signal(str)  # Error message

    def __init__(self, url: str, dest_folder: Path, isolate_piano: bool = False) -> None:
        super().__init__()
        self._url = url
        self._dest_folder = dest_folder
        self._isolate_piano = isolate_piano

    def run(self) -> None:
        """Run the import pipeline based on URL type."""
        from maestro.importers.online_sequencer import extract_sequence_id
        from maestro.importers.youtube import extract_video_id

        try:
            sequence_id = extract_sequence_id(self._url)
            video_id = extract_video_id(self._url)

            if sequence_id:
                self._import_online_sequencer(sequence_id)
            elif video_id:
                self._import_youtube()
            else:
                self.error.emit(
                    "Unsupported URL. Paste an OnlineSequencer or YouTube link."
                )
        except Exception as e:
            self.error.emit(str(e))

    def _import_online_sequencer(self, sequence_id: str) -> None:
        from maestro.importers.online_sequencer import download_midi, fetch_song_title

        self.progress.emit("Fetching song info...")
        title = fetch_song_title(sequence_id)

        self.progress.emit("Downloading MIDI...")
        result = download_midi(sequence_id, self._dest_folder, title)

        self.finished.emit(result.name)

    def _import_youtube(self) -> None:
        from maestro.importers.youtube import (
            download_audio,
            isolate_piano,
            transcribe_audio,
        )

        self.progress.emit("Downloading audio...")
        audio_path, title = download_audio(self._url, self._dest_folder)

        if self._isolate_piano:
            self.progress.emit("Isolating piano...")
            try:
                audio_path = isolate_piano(audio_path, self._dest_folder)
            except Exception:
                self.progress.emit("Piano isolation failed, using full audio...")

        self.progress.emit("Transcribing to MIDI...")
        result = transcribe_audio(audio_path, self._dest_folder, title)

        self.finished.emit(result.name)


class DemucsDownloadWorker(QThread):
    """Background thread that downloads the demucs model."""

    progress = Signal(str)  # Status text
    finished = Signal()
    error = Signal(str)  # Error message

    def __init__(self, model_dir: Path) -> None:
        super().__init__()
        self._model_dir = model_dir

    def run(self) -> None:
        """Download and set up the demucs model."""
        import subprocess

        try:
            self.progress.emit("Installing demucs model...")
            self._model_dir.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                ["pip", "install", "demucs", "--target", str(self._model_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.error.emit(f"Model download failed: {result.stderr[:200]}")
                return

            self.progress.emit("Model installed successfully")
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Download failed: {e}")
