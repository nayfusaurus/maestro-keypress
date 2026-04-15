"""Now Playing panel with song metadata, progress bar, and time display."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.utils import format_time
from maestro.logger import setup_logger


def _format_size(size_bytes: int) -> str:
    """Format file size in B / KB / MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


class NowPlayingPanel(QWidget):
    """Displays selected song name, metadata grid, progress bar, and time.

    The panel has three visual modes:
      - No song: single "No song loaded" label.
      - Valid song: name + metadata grid (BPM, Notes, Size, Modified).
      - Pending/Invalid: name + single status line ("Validating..."/etc).

    Progress row (time / bar / time) is always present.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = setup_logger()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Song name
        self._song_label = QLabel("No song loaded")
        self._song_label.setProperty("class", "caption")
        self._song_label.setWordWrap(True)
        self._song_label.setMinimumWidth(1)
        layout.addWidget(self._song_label)

        # Metadata grid (hidden until a valid song is shown)
        self._meta_widget = QWidget()
        grid = QGridLayout(self._meta_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)

        def _field(row: int, label_text: str) -> QLabel:
            lbl = QLabel(label_text)
            lbl.setProperty("class", "caption")
            grid.addWidget(lbl, row, 0)
            value = QLabel("")
            value.setProperty("class", "caption")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(value, row, 1)
            return value

        self._bpm_value = _field(0, "BPM")
        self._notes_value = _field(1, "Notes")
        self._size_value = _field(2, "Size")
        self._modified_value = _field(3, "Modified")
        grid.setColumnStretch(1, 1)

        self._meta_widget.setVisible(False)
        layout.addWidget(self._meta_widget)

        # Status label (used for pending / invalid)
        self._status_label = QLabel("")
        self._status_label.setProperty("class", "caption")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # Progress row: current time | progress bar | total time
        progress_row = QHBoxLayout()
        progress_row.setSpacing(12)

        self._time_current = QLabel("0:00")
        self._time_current.setProperty("class", "caption")
        self._time_current.setFixedWidth(44)
        progress_row.addWidget(self._time_current)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1000)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(4)
        progress_row.addWidget(self._progress_bar, stretch=1)

        self._time_total = QLabel("0:00")
        self._time_total.setProperty("class", "caption")
        self._time_total.setFixedWidth(44)
        self._time_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        progress_row.addWidget(self._time_total)

        layout.addLayout(progress_row)

    def update_metadata(
        self,
        song: Path | None,
        status: str,
        info: dict | None,
        compatibility: tuple[int, int],
    ) -> None:
        """Update the panel to reflect the given song and its metadata.

        Args:
            song: Path to the song, or None for the empty state.
            status: "valid" / "pending" / "invalid".
            info: Dict with "bpm", "note_count" (from MIDI validation),
                or None when not yet available.
            compatibility: (playable, total) from the layout-compat worker.
        """
        if song is None:
            self._song_label.setText("No song loaded")
            self._meta_widget.setVisible(False)
            self._status_label.setVisible(False)
            return

        # Insert zero-width spaces after underscores so Qt's word-wrap
        # (which follows UAX #14 and doesn't break on '_') has break points.
        self._song_label.setText(song.stem.replace("_", "_\u200b"))

        # Pending (or valid-but-no-info-yet) → show "Validating…"
        if status == "pending" or (status == "valid" and info is None):
            self._status_label.setText("Validating\u2026")
            self._status_label.setVisible(True)
            self._meta_widget.setVisible(False)
            return

        if status == "invalid":
            self._status_label.setText("Invalid MIDI file")
            self._status_label.setVisible(True)
            self._meta_widget.setVisible(False)
            return

        # status == "valid" with info present (guarded above).
        assert info is not None  # noqa: S101
        self._status_label.setVisible(False)
        self._meta_widget.setVisible(True)

        bpm = int(info.get("bpm", 0))
        note_count = int(info.get("note_count", 0))
        playable, total = compatibility
        self._bpm_value.setText(str(bpm))
        if total > 0:
            pct = round(playable / total * 100)
            self._notes_value.setText(f"{note_count} ({playable} playable \u00b7 {pct}%)")
        else:
            self._notes_value.setText(str(note_count))

        try:
            st = song.stat()
            self._size_value.setText(_format_size(st.st_size))
            self._modified_value.setText(datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"))
        except OSError as e:
            self._logger.warning(f"stat() failed for {song}: {e}")
            self._size_value.setText("\u2014")
            self._modified_value.setText("\u2014")

    def update_progress(self, position: float, duration: float) -> None:
        """Update the progress bar and time display."""
        if duration > 0:
            progress = int((position / duration) * 1000)
            self._progress_bar.setValue(progress)
        else:
            self._progress_bar.setValue(0)

        self._time_current.setText(format_time(position))
        self._time_total.setText(format_time(duration))
