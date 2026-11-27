# SPDX-License-Identifier: MPL-2.0
"""Piano keyboard used for playback statistics."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QToolTip, QWidget

from maestro.gui.theme import COLORS
from maestro.stats import midi_to_name


class NoteKeyboard(QWidget):
    def __init__(self, counts: dict[int, int]):
        super().__init__()
        self.counts = counts
        self.setFixedHeight(78)
        self.setMouseTracking(True)
        self.setAccessibleName("Piano note frequencies")
        self.setAccessibleDescription(", ".join(self.note_text(n) for n in sorted(counts)))

    def note_text(self, note: int) -> str:
        return f"{midi_to_name(note)} · {self.counts.get(note, 0):,} hits"

    def keys(self) -> list[tuple[int, QRectF, bool]]:
        first = min(self.counts, default=60) // 12 * 12
        last = max(self.counts, default=71) // 12 * 12 + 11
        width = self.width() / (7 * ((last - first) // 12 + 1))
        whites: list[tuple[int, QRectF, bool]] = []
        blacks = []
        for note in range(first, last + 1):
            if note % 12 in (1, 3, 6, 8, 10):
                blacks.append((note, QRectF((len(whites) - 0.3) * width, 0, width * 0.6, 46), True))
            else:
                whites.append((note, QRectF(len(whites) * width, 0, width, 76), False))
        return whites + blacks

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(QColor(COLORS["surface_active"]))
        highest = max(self.counts.values(), default=1)
        for note, rect, black in self.keys():
            painter.setBrush(QColor("#303445" if black else "#eef0f5"))
            painter.drawRect(rect)
            if self.counts.get(note):
                ink = QColor(COLORS["accent"])
                ink.setAlphaF(0.25 + 0.75 * self.counts[note] / highest)
                painter.fillRect(rect.adjusted(1, 1, -1, -1), ink)
            if note % 12 == 0 and rect.width() > 23:
                painter.save()
                painter.setPen(QColor("#282a36"))
                painter.drawText(
                    rect,
                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                    midi_to_name(note),
                )
                painter.restore()
        painter.end()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        for note, rect, _ in reversed(self.keys()):
            if rect.contains(event.position()):
                QToolTip.showText(event.globalPosition().toPoint(), self.note_text(note), self)
                break
