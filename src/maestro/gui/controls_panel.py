"""Playback control buttons panel."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ControlsPanel(QWidget):
    """Panel with Play, Stop, and Favorite buttons."""

    play_clicked = Signal()
    stop_clicked = Signal()
    favorite_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # Play — PRIMARY button (accent colored)
        self._play_btn = QPushButton("Play")
        self._play_btn.setProperty("class", "primary")
        self._play_btn.setMinimumHeight(32)
        self._play_btn.clicked.connect(self.play_clicked)
        layout.addWidget(self._play_btn, stretch=1)

        # Stop — SECONDARY button (default surface style)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setMinimumHeight(32)
        self._stop_btn.clicked.connect(self.stop_clicked)
        layout.addWidget(self._stop_btn, stretch=1)

        # Favorite — GHOST button (icon-only)
        self._fav_btn = QPushButton("\u2606")  # Empty star
        self._fav_btn.setProperty("class", "ghost")
        self._fav_btn.setFixedSize(32, 32)
        self._fav_btn.clicked.connect(self.favorite_clicked)
        layout.addWidget(self._fav_btn)

    def set_favorite(self, is_favorite: bool) -> None:
        """Update the favorite button star."""
        self._fav_btn.setText("\u2605" if is_favorite else "\u2606")
