"""Icon rail navigation sidebar widget.

A 56px-wide vertical bar with page icons at the top and an exit icon pinned
to the bottom. All icons are drawn with QPainter (no icon library).
"""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from maestro.gui.theme import COLORS

# ---------------------------------------------------------------------------
# Page constants
# ---------------------------------------------------------------------------

PAGE_DASHBOARD = 0
PAGE_SETTINGS = 1
PAGE_INFO = 2
PAGE_LOG = 3

_ICON_LABELS = ["Dashboard", "Settings", "About", "Error Log", "Exit"]

# ---------------------------------------------------------------------------
# Sizing constants
# ---------------------------------------------------------------------------

_RAIL_WIDTH = 80
_ICON_CELL_HEIGHT = 64
_ICON_SIZE = 36  # icon drawing area (centered in cell)
_ACTIVE_BAR_WIDTH = 4
_BADGE_RADIUS = 5  # 10px dot diameter


class IconRail(QWidget):
    """Vertical icon-rail navigation sidebar."""

    page_changed = Signal(int)
    exit_clicked = Signal()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active: int = PAGE_DASHBOARD
        self._hover: int = -1  # -1 = none, 0..3 = page icons, 4 = exit
        self._disabled_pages: set[int] = set()
        self._badges: set[int] = set()
        self._page_count = 4  # Dashboard, Settings, Info, Log

        self.setFixedWidth(_RAIL_WIDTH)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def active_index(self) -> int:
        """Return the index of the currently active page."""
        return self._active

    def set_active(self, index: int) -> None:
        """Set the active page if it is not disabled."""
        if index < 0 or index >= self._page_count:
            return
        if index in self._disabled_pages:
            return
        if index != self._active:
            self._active = index
            self.page_changed.emit(index)
            self.update()

    def page_count(self) -> int:
        """Return the number of navigable pages."""
        return self._page_count

    def set_disabled_pages(self, pages: set[int]) -> None:
        """Set which page indices are disabled (non-clickable, dimmed)."""
        self._disabled_pages = set(pages)
        self.update()

    def set_badge(self, index: int, show: bool) -> None:
        """Show or hide a notification badge on a page icon."""
        if show:
            self._badges.add(index)
        else:
            self._badges.discard(index)
        self.update()

    def fixedWidth(self) -> int:  # noqa: N802 — Qt naming convention
        """Return the fixed rail width."""
        return _RAIL_WIDTH

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _icon_rect(self, index: int) -> QRectF:
        """Return the bounding rect for page icon *index* (0..3)."""
        y = index * _ICON_CELL_HEIGHT
        return QRectF(0, y, _RAIL_WIDTH, _ICON_CELL_HEIGHT)

    def _exit_rect(self) -> QRectF:
        """Return the bounding rect for the exit icon (pinned to bottom)."""
        return QRectF(0, self.height() - _ICON_CELL_HEIGHT, _RAIL_WIDTH, _ICON_CELL_HEIGHT)

    def _hit_test(self, y: float) -> int:
        """Return icon index at *y*, or -1 if nothing hit.

        0..3 = page icons, 4 = exit.
        """
        for i in range(self._page_count):
            if self._icon_rect(i).contains(QPointF(_RAIL_WIDTH / 2, y)):
                return i
        if self._exit_rect().contains(QPointF(_RAIL_WIDTH / 2, y)):
            return self._page_count  # exit index
        return -1

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        idx = self._hit_test(event.position().y())
        if idx == self._page_count:
            self.exit_clicked.emit()
        elif 0 <= idx < self._page_count:
            self.set_active(idx)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        old_hover = self._hover
        self._hover = self._hit_test(event.position().y())
        if self._hover != old_hover:
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def event(self, ev: QEvent) -> bool:
        """Handle QEvent.ToolTip to show icon labels."""
        if ev.type() == QEvent.Type.ToolTip:
            idx = self._hit_test(ev.pos().y())  # type: ignore[union-attr]
            if 0 <= idx < len(_ICON_LABELS):
                QToolTip.showText(ev.globalPos(), _ICON_LABELS[idx], self)  # type: ignore[union-attr]
            else:
                QToolTip.hideText()
            return True
        return super().event(ev)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Rail background
        painter.fillRect(self.rect(), QColor(COLORS["surface0"]))

        # Page icons
        for i in range(self._page_count):
            self._paint_icon(painter, i)

        # Exit icon (pinned to bottom)
        self._paint_exit(painter)

        painter.end()

    def _paint_icon(self, painter: QPainter, index: int) -> None:
        """Paint a single page icon cell."""
        rect = self._icon_rect(index)
        is_active = index == self._active
        is_hover = index == self._hover
        is_disabled = index in self._disabled_pages

        # Hover background
        if is_hover and not is_disabled:
            painter.fillRect(rect.toRect(), QColor(COLORS["surface2"]))

        # Active bar
        if is_active:
            bar = QRectF(0, rect.y() + 8, _ACTIVE_BAR_WIDTH, rect.height() - 16)
            painter.fillRect(bar.toRect(), QColor(COLORS["accent"]))

        # Icon color
        if is_disabled:
            color = QColor(COLORS["surface_active"])
        elif is_active:
            color = QColor(COLORS["accent"])
        else:
            color = QColor(COLORS["subtext"])

        # Icon center
        cx = rect.center().x()
        cy = rect.center().y()

        # Draw the appropriate icon
        draw_fn = [
            self._draw_home_icon,
            self._draw_gear_icon,
            self._draw_info_icon,
            self._draw_log_icon,
        ][index]
        draw_fn(painter, cx, cy, color)

        # Notification badge
        if index in self._badges:
            bx = cx + _ICON_SIZE / 2 - 1
            by = cy - _ICON_SIZE / 2 + 1
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["accent"]))
            painter.drawEllipse(QPointF(bx, by), _BADGE_RADIUS, _BADGE_RADIUS)

    def _paint_exit(self, painter: QPainter) -> None:
        """Paint the exit icon cell at the bottom."""
        rect = self._exit_rect()
        is_hover = self._hover == self._page_count

        if is_hover:
            painter.fillRect(rect.toRect(), QColor(COLORS["surface2"]))

        # Exit icon turns red on hover, otherwise subtext color
        color = QColor(COLORS["red"]) if is_hover else QColor(COLORS["subtext"])

        cx = rect.center().x()
        cy = rect.center().y()
        self._draw_exit_icon(painter, cx, cy, color)

    # ------------------------------------------------------------------
    # Icon drawing helpers (QPainter, no icon library)
    # ------------------------------------------------------------------

    def _draw_home_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        """Draw a simple house icon: a triangle roof + rectangle body."""
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        s = _ICON_SIZE / 2  # half-size

        # Roof (triangle)
        roof_top = QPointF(cx, cy - s + 2)
        roof_left = QPointF(cx - s + 2, cy - 2)
        roof_right = QPointF(cx + s - 2, cy - 2)
        p.drawLine(roof_top, roof_left)
        p.drawLine(roof_top, roof_right)

        # Body (rectangle below roof)
        body = QRectF(cx - s * 0.6, cy - 2, s * 1.2, s - 1)
        p.drawRect(body)

    def _draw_gear_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        """Draw a gear icon: outer toothed circle + inner circle."""
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        r_outer = _ICON_SIZE / 2 - 2
        r_inner = r_outer * 0.45
        teeth = 8
        tooth_len = 4.5

        # Draw teeth as short radial lines
        for i in range(teeth):
            angle = 2 * math.pi * i / teeth
            x1 = cx + (r_outer - tooth_len) * math.cos(angle)
            y1 = cy + (r_outer - tooth_len) * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Outer circle
        p.drawEllipse(QPointF(cx, cy), r_outer - tooth_len, r_outer - tooth_len)

        # Inner circle (hub)
        p.drawEllipse(QPointF(cx, cy), r_inner, r_inner)

    def _draw_info_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        """Draw an info icon: circle with 'i' inside."""
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        r = _ICON_SIZE / 2 - 2

        # Outer circle
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Dot above the i
        dot_pen = QPen(color, 3.5)
        dot_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(dot_pen)
        p.drawPoint(QPointF(cx, cy - r * 0.35))

        # Stem of the i
        p.setPen(pen)
        p.drawLine(QPointF(cx, cy - r * 0.05), QPointF(cx, cy + r * 0.5))

    def _draw_log_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        """Draw a document/log icon: rectangle with lines inside."""
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        s = _ICON_SIZE / 2 - 2
        w = s * 1.3
        h = s * 1.6

        # Document outline
        doc = QRectF(cx - w / 2, cy - h / 2, w, h)
        p.drawRect(doc)

        # Text lines inside
        line_pen = QPen(color, 1.8)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(line_pen)
        lx1 = cx - w * 0.3
        lx2 = cx + w * 0.3
        for i, frac in enumerate([0.3, 0.5, 0.7]):
            ly = doc.top() + h * frac
            # Make the last line shorter for visual interest
            end_x = lx2 if i < 2 else cx + w * 0.1
            p.drawLine(QPointF(lx1, ly), QPointF(end_x, ly))

    def _draw_exit_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        """Draw an exit/door icon: door frame with arrow pointing out."""
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        s = _ICON_SIZE / 2 - 2

        # Door frame (open on the right side)
        p.drawLine(QPointF(cx - s, cy - s), QPointF(cx - s, cy + s))  # left
        p.drawLine(QPointF(cx - s, cy - s), QPointF(cx + s * 0.2, cy - s))  # top
        p.drawLine(QPointF(cx - s, cy + s), QPointF(cx + s * 0.2, cy + s))  # bottom

        # Arrow pointing right (exit direction)
        arrow_y = cy
        arrow_start = cx - s * 0.1
        arrow_end = cx + s
        p.drawLine(QPointF(arrow_start, arrow_y), QPointF(arrow_end, arrow_y))
        # Arrowhead
        p.drawLine(QPointF(arrow_end, arrow_y), QPointF(arrow_end - s * 0.35, arrow_y - s * 0.35))
        p.drawLine(QPointF(arrow_end, arrow_y), QPointF(arrow_end - s * 0.35, arrow_y + s * 0.35))
