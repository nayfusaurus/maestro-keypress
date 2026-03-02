"""Now Playing panel with transport-style progress bar and time display."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from maestro.gui.utils import format_time


class NowPlayingPanel(QWidget):
    """Displays current song name, progress bar, and time in transport style."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Song name
        self._song_label = QLabel("No song loaded")
        self._song_label.setProperty("class", "caption")
        self._song_label.setWordWrap(True)
        layout.addWidget(self._song_label)

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

    def update_song(self, name: str) -> None:
        """Update the displayed song name."""
        self._song_label.setText(name if name else "No song loaded")

    def update_progress(self, position: float, duration: float) -> None:
        """Update the progress bar and time display."""
        if duration > 0:
            progress = int((position / duration) * 1000)
            self._progress_bar.setValue(progress)
        else:
            self._progress_bar.setValue(0)

        self._time_current.setText(format_time(position))
        self._time_total.setText(format_time(duration))
