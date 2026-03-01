"""Lightweight splash screen shown during app startup.

Must NOT import any other maestro modules — it loads before them.
Colors are hardcoded to match the Catppuccin Mocha dark theme.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget


class SplashScreen(QWidget):
    """Frameless splash window with progress bar and status text."""

    _W = 360
    _H = 180
    _RADIUS = 16
    _BAR_H = 4
    _BAR_MARGIN = 40

    # Hardcoded Catppuccin Mocha colors (can't import theme.py yet)
    _BG = "#1e1e2e"
    _SURFACE = "#3b3d52"
    _TEXT = "#cdd6f4"
    _SUBTEXT = "#bac2de"
    _ACCENT = "#89b4fa"

    def __init__(self) -> None:
        super().__init__(None)
        self._progress = 0
        self._status = "Starting..."

        self.setFixedSize(self._W, self._H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Center on primary screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self._W) // 2,
                geo.y() + (geo.height() - self._H) // 2,
            )

    def set_progress(self, percent: int, text: str) -> None:
        """Update progress bar and status text, then repaint."""
        self._progress = max(0, min(100, percent))
        self._status = text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Rounded card background
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, self._W, self._H, self._RADIUS, self._RADIUS)
        p.fillPath(path, QColor(self._BG))

        # Subtle border
        p.setPen(QColor(self._SURFACE))
        p.drawRoundedRect(0, 0, self._W - 1, self._H - 1, self._RADIUS, self._RADIUS)

        # Title
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setWeight(QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(QColor(self._TEXT))
        p.drawText(0, 40, self._W, 40, Qt.AlignmentFlag.AlignCenter, "Maestro")

        # Status text
        status_font = QFont()
        status_font.setPointSize(10)
        p.setFont(status_font)
        p.setPen(QColor(self._SUBTEXT))
        p.drawText(
            self._BAR_MARGIN, 90, self._W - 2 * self._BAR_MARGIN, 24,
            Qt.AlignmentFlag.AlignCenter, self._status,
        )

        # Progress bar track
        bar_y = 124
        bar_w = self._W - 2 * self._BAR_MARGIN
        track_path = QPainterPath()
        track_path.addRoundedRect(
            self._BAR_MARGIN, bar_y, bar_w, self._BAR_H, 2, 2,
        )
        p.fillPath(track_path, QColor(self._SURFACE))

        # Progress bar fill
        if self._progress > 0:
            fill_w = int(bar_w * self._progress / 100)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(
                self._BAR_MARGIN, bar_y, fill_w, self._BAR_H, 2, 2,
            )
            p.fillPath(fill_path, QColor(self._ACCENT))

        # Percentage text
        pct_font = QFont()
        pct_font.setPointSize(9)
        p.setFont(pct_font)
        p.setPen(QColor(self._SUBTEXT))
        p.drawText(
            self._BAR_MARGIN, 134, bar_w, 20,
            Qt.AlignmentFlag.AlignCenter, f"{self._progress}%",
        )

        p.end()
