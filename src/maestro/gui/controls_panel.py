"""Playback control buttons panel."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from maestro.gui.theme import COLORS


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

        # Favorite — explicit font + inline style to guarantee visibility
        # (QSS attribute selectors can fail to override base QPushButton
        # font-size on some platforms, making the star invisible).
        self._fav_btn = QPushButton("\u2605")
        star_font = QFont()
        star_font.setPointSize(20)
        self._fav_btn.setFont(star_font)
        self._fav_btn.setFixedSize(40, 40)
        self._fav_btn.setToolTip("Toggle favorite")
        self._fav_btn.setCursor(self._play_btn.cursor())
        self._fav_btn.clicked.connect(self.favorite_clicked)
        self._is_favorite = False
        self._apply_fav_style(False)
        layout.addWidget(self._fav_btn)

    def set_favorite(self, is_favorite: bool) -> None:
        """Update the favorite button visual state."""
        self._is_favorite = is_favorite
        self._apply_fav_style(is_favorite)

    def refresh_style(self) -> None:
        """Re-apply favorite button colors after a theme change."""
        self._apply_fav_style(self._is_favorite)

    def _apply_fav_style(self, on: bool) -> None:
        """Set the favorite button's color and border directly."""
        if on:
            fg = COLORS["yellow"]
            border = f"2px solid {COLORS['yellow']}"
            bg = COLORS["surface1"]
        else:
            fg = COLORS["text"]
            border = f"1px solid {COLORS['surface_hover']}"
            bg = COLORS["surface2"]
        self._fav_btn.setStyleSheet(
            f"QPushButton {{ color: {fg}; background-color: {bg};"
            f" border: {border}; border-radius: 8px; padding: 0; }}"
            f" QPushButton:hover {{ color: {COLORS['yellow']};"
            f" background-color: {COLORS['surface_hover']};"
            f" border-color: {COLORS['yellow']}; }}"
        )
