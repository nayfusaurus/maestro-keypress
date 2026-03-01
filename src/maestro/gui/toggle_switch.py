"""Animated toggle switch widget for the Maestro GUI.

A custom QWidget that renders as an iOS-style toggle switch with smooth
animation between ON and OFF states.  Uses theme colors from theme.py.
"""

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from maestro.gui.theme import COLORS

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
_WIDTH = 40
_HEIGHT = 22
_TRACK_RADIUS = _HEIGHT // 2  # 11px — fully rounded ends
_THUMB_DIAMETER = 16
_THUMB_RADIUS = _THUMB_DIAMETER // 2  # 8px
_INSET = 3  # gap between track edge and thumb center path

# Thumb x-positions (centre of circle)
_THUMB_X_OFF = float(_INSET + _THUMB_RADIUS)  # 3 + 8 = 11
_THUMB_X_ON = float(_WIDTH - _INSET - _THUMB_RADIUS)  # 40 - 3 - 8 = 29


class ToggleSwitch(QWidget):
    """A 40x22 animated toggle switch.

    Signals
    -------
    toggled(bool)
        Emitted whenever the checked state changes.
    """

    toggled = Signal(bool)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, parent: QWidget | None = None, *, checked: bool = False) -> None:
        super().__init__(parent)
        self._checked: bool = checked
        self._thumb_x: float = _THUMB_X_ON if checked else _THUMB_X_OFF

        # Animation for the thumb slide
        self._animation = QPropertyAnimation(self, b"thumb_x", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setFixedSize(_WIDTH, _HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def isChecked(self) -> bool:  # noqa: N802
        """Return the current checked state."""
        return self._checked

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        """Set the checked state, animating the thumb and emitting *toggled*."""
        if checked == self._checked:
            return
        self._checked = checked
        self._animate_thumb()
        self.toggled.emit(self._checked)
        self.update()

    # ------------------------------------------------------------------
    # Size hint
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(_WIDTH, _HEIGHT)

    # ------------------------------------------------------------------
    # Qt Property for animation
    # ------------------------------------------------------------------

    def _get_thumb_x(self) -> float:
        return self._thumb_x

    def _set_thumb_x(self, value: float) -> None:
        self._thumb_x = value
        self.update()

    thumb_x = Property(float, _get_thumb_x, _set_thumb_x)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Toggle state on left-click when enabled."""
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw the track and thumb using current theme colors."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- Pick colors based on state ---
        if not self.isEnabled():
            track_color = QColor(COLORS["surface1"])
            thumb_color = QColor(COLORS["overlay"])
        elif self._checked:
            track_color = QColor(COLORS["accent"])
            thumb_color = QColor(COLORS["base"])
        else:
            track_color = QColor(COLORS["surface_active"])
            thumb_color = QColor(COLORS["overlay"])

        # --- Draw track (rounded rectangle) ---
        track_path = QPainterPath()
        track_path.addRoundedRect(0.0, 0.0, float(_WIDTH), float(_HEIGHT),
                                  _TRACK_RADIUS, _TRACK_RADIUS)
        painter.setPen(track_color)
        painter.setBrush(track_color)
        painter.drawPath(track_path)

        # --- Draw thumb (circle) ---
        thumb_y = float(_HEIGHT) / 2.0
        painter.setPen(thumb_color)
        painter.setBrush(thumb_color)
        painter.drawEllipse(
            int(self._thumb_x - _THUMB_RADIUS),
            int(thumb_y - _THUMB_RADIUS),
            _THUMB_DIAMETER,
            _THUMB_DIAMETER,
        )

        painter.end()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _animate_thumb(self) -> None:
        """Animate the thumb from its current x to the target position."""
        self._animation.stop()
        self._animation.setStartValue(self._thumb_x)
        self._animation.setEndValue(_THUMB_X_ON if self._checked else _THUMB_X_OFF)
        self._animation.start()
