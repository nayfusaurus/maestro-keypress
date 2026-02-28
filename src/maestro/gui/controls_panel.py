"""Playback control buttons panel."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ControlsPanel(QWidget):
    """Panel with Play, Stop, Favorite, and Refresh buttons."""

    play_clicked = Signal()
    stop_clicked = Signal()
    favorite_clicked = Signal()
    refresh_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Play — PRIMARY button (accent colored, larger)
        self._play_btn = QPushButton("Play")
        self._play_btn.setProperty("class", "primary")
        self._play_btn.setMinimumHeight(36)
        self._play_btn.clicked.connect(self.play_clicked)
        layout.addWidget(self._play_btn, stretch=1)

        # Stop — SECONDARY button (default surface style)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setMinimumHeight(36)
        self._stop_btn.clicked.connect(self.stop_clicked)
        layout.addWidget(self._stop_btn, stretch=1)

        # Favorite — GHOST button (icon-only)
        self._fav_btn = QPushButton("\u2606")  # Empty star
        self._fav_btn.setProperty("class", "ghost")
        self._fav_btn.setFixedSize(36, 36)
        self._fav_btn.clicked.connect(self.favorite_clicked)
        layout.addWidget(self._fav_btn)

        # Refresh — GHOST button (icon-only)
        self._refresh_btn = QPushButton("\u21bb")  # ↻
        self._refresh_btn.setProperty("class", "ghost")
        self._refresh_btn.setFixedSize(36, 36)
        self._refresh_btn.clicked.connect(self.refresh_clicked)
        layout.addWidget(self._refresh_btn)

    def set_favorite(self, is_favorite: bool) -> None:
        """Update the favorite button star."""
        self._fav_btn.setText("\u2605" if is_favorite else "\u2606")
