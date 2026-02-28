"""Piano roll preview widget showing upcoming notes."""

from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from maestro.gui.theme import COLORS


class PianoRollWidget(QWidget):
    """Custom-painted widget that displays upcoming MIDI notes as a scrolling piano roll."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(100)
        self._notes: list = []
        self._current_pos: float = 0.0
        self._lookahead: float = 5.0

    def set_notes(self, notes: list, current_pos: float, lookahead: float) -> None:
        """Update the notes to display and trigger a repaint."""
        self._notes = notes
        self._current_pos = current_pos
        self._lookahead = lookahead
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw the piano roll with accent-colored notes, grid lines, and playhead."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(COLORS["surface0"]))

        # Subtle horizontal grid lines at ~12px intervals, 15% opacity
        grid_color = QColor(COLORS["overlay"])
        grid_color.setAlpha(38)  # 15% of 255
        grid_pen = QPen(grid_color, 1)
        painter.setPen(grid_pen)
        y_grid = 12
        while y_grid < h:
            painter.drawLine(0, y_grid, w, y_grid)
            y_grid += 12

        # Playhead line — accent color, 1px wide
        pen = QPen(QColor(COLORS["accent"]), 1)
        painter.setPen(pen)
        painter.drawLine(2, 0, 2, h)

        if not self._notes:
            painter.end()
            return

        # Find note range for vertical scaling
        min_note = min(n.midi_note for n in self._notes)
        max_note = max(n.midi_note for n in self._notes)
        note_range = max(max_note - min_note, 12)  # At least one octave

        # Note fill: accent color at 30% opacity
        fill_color = QColor(COLORS["accent"])
        fill_color.setAlpha(77)  # 30% of 255

        # Note outline: accent color at full opacity, 1px
        outline_color = QColor(COLORS["accent"])
        outline_pen = QPen(outline_color, 1)

        for note in self._notes:
            # X position based on time
            time_offset = note.time - self._current_pos
            x = 5 + (time_offset / self._lookahead) * (w - 10)

            # Width based on duration (min 3px)
            width = max(3.0, (note.duration / self._lookahead) * (w - 10))

            # Y position based on pitch (higher = top)
            y_ratio = 1 - ((note.midi_note - min_note) / note_range)
            y = 5 + y_ratio * (h - 10)

            # Draw note rectangle — accent fill + accent outline
            painter.fillRect(int(x), int(y) - 3, int(width), 6, fill_color)
            painter.setPen(outline_pen)
            painter.drawRect(int(x), int(y) - 3, int(width), 6)

        painter.end()
