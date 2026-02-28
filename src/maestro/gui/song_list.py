"""Song list widget with custom delegate for rich two-line song items."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from maestro.gui.utils import get_songs_from_folder


class SongItemDelegate(QStyledItemDelegate):
    """Custom delegate for painting rich two-line song items.

    Each item displays:
      - Left accent bar (3px, color-coded by validation status)
      - Favorite star (filled gold or empty dim)
      - Line 1: Song name (10pt) left-aligned, duration right-aligned
      - Line 2: Metadata caption (9pt, dim): BPM and note count
    """

    def sizeHint(  # noqa: N802
        self, option: QStyleOptionViewItem, index: "QModelIndex"  # noqa: F821
    ) -> QSize:
        return QSize(option.rect.width(), 52)

    def paint(  # noqa: N802
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: "QModelIndex",  # noqa: F821
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect
        meta = index.data(Qt.ItemDataRole.UserRole)
        if meta is None:
            meta = {
                "stem": index.data(),
                "status": "pending",
                "is_favorite": False,
                "duration": 0,
                "bpm": 0,
                "note_count": 0,
            }

        # Background
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if is_selected:
            painter.fillRect(rect, QColor("#3b3d52"))
        elif is_hovered:
            painter.fillRect(rect, QColor("#313244"))

        # Left accent bar (3px)
        status = meta.get("status", "pending")
        accent_colors = {"valid": "#40a02b", "invalid": "#d32f2f", "pending": "#6c7086"}
        accent = QColor(accent_colors.get(status, "#6c7086"))
        painter.fillRect(rect.x(), rect.y(), 3, rect.height(), accent)

        # Favorite star
        star_x = rect.x() + 12
        star_y = rect.y() + rect.height() // 2
        if meta.get("is_favorite"):
            painter.setPen(QColor("#f9e2af"))
            star_char = "\u2605"
        else:
            painter.setPen(QColor("#6c7086"))
            star_char = "\u2606"
        star_font = QFont()
        star_font.setPointSize(12)
        painter.setFont(star_font)
        painter.drawText(star_x, star_y + 5, star_char)

        # Line 1: Song name
        name_font = QFont()
        name_font.setPointSize(10)
        painter.setFont(name_font)
        painter.setPen(QColor("#cdd6f4"))
        name_rect_x = rect.x() + 32
        name_y = rect.y() + 22
        # Leave room for duration on the right
        name_width = rect.width() - 32 - 50
        text = painter.fontMetrics().elidedText(
            meta["stem"], Qt.TextElideMode.ElideRight, name_width
        )
        painter.drawText(name_rect_x, name_y, text)

        # Duration (right-aligned, caption style)
        duration = meta.get("duration", 0)
        if duration > 0:
            minutes = int(duration // 60)
            secs = int(duration % 60)
            dur_text = f"{minutes}:{secs:02d}"
            caption_font = QFont()
            caption_font.setPointSize(9)
            painter.setFont(caption_font)
            painter.setPen(QColor("#6c7086"))
            dur_width = painter.fontMetrics().horizontalAdvance(dur_text)
            painter.drawText(rect.right() - dur_width - 12, name_y, dur_text)

        # Line 2: Metadata
        bpm = meta.get("bpm", 0)
        note_count = meta.get("note_count", 0)
        if bpm > 0 or note_count > 0:
            meta_parts: list[str] = []
            if bpm > 0:
                meta_parts.append(f"{bpm} BPM")
            if note_count > 0:
                meta_parts.append(f"{note_count} notes")
            meta_text = " \u00b7 ".join(meta_parts)
            caption_font = QFont()
            caption_font.setPointSize(9)
            painter.setFont(caption_font)
            painter.setPen(QColor("#6c7086"))
            painter.drawText(name_rect_x, rect.y() + 40, meta_text)

        painter.restore()


class SongListWidget(QListWidget):
    """List widget that displays MIDI songs with rich two-line items.

    Uses SongItemDelegate for custom painting with:
    - Color-coded accent bars (green=valid, red=invalid, gray=pending)
    - Favorite stars
    - Song metadata (duration, BPM, note count)

    Sort order: favorites > valid > pending > invalid (alphabetical within each group).
    """

    song_selected = Signal(object)  # Path or None
    song_double_clicked = Signal(object)  # Path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._songs: list[Path] = []
        self._filtered_songs: list[Path] = []
        self._validation_results: dict[str, str] = {}
        self._song_info: dict[str, dict] = {}
        self._song_notes: dict[str, list] = {}
        self._validation_cache: dict[str, tuple[float, bool]] = {}
        self._favorites: list[str] = []

        self._delegate = SongItemDelegate(self)
        self.setItemDelegate(self._delegate)

        self.currentItemChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_double_click)

    def load_songs(self, folder: Path) -> None:
        """Load songs from a folder."""
        self._songs = get_songs_from_folder(folder)

    def get_songs(self) -> list[Path]:
        """Get the full list of loaded songs."""
        return self._songs

    def get_filtered_songs(self) -> list[Path]:
        """Get the current filtered song list."""
        return self._filtered_songs

    def get_selected_song(self) -> Path | None:
        """Get the currently selected song path."""
        row = self.currentRow()
        if row < 0 or row >= len(self._filtered_songs):
            return None
        return self._filtered_songs[row]

    def apply_filter(
        self, search_term: str, favorites: list[str], validation_results: dict[str, str]
    ) -> None:
        """Apply search filter and re-sort the song list."""
        self._validation_results = validation_results
        self._favorites = favorites
        search_lower = search_term.lower()

        if search_lower:
            filtered = [s for s in self._songs if search_lower in s.stem.lower()]
        else:
            filtered = self._songs.copy()

        # Sort: favorites first, then valid/pending/invalid, each alphabetical
        def sort_key(song: Path):
            is_fav = 0 if song.stem in favorites else 1
            status = self._validation_results.get(str(song), "pending")
            order = {"valid": 0, "pending": 1, "invalid": 2}
            return (is_fav, order.get(status, 1), song.stem.lower())

        self._filtered_songs = sorted(filtered, key=sort_key)
        self._rebuild_list()

    def on_song_validated(self, path_str: str, status: str, info: dict, notes: list) -> None:
        """Handle validation result for a single song."""
        self._validation_results[path_str] = status
        self._song_info[path_str] = info
        self._song_notes[path_str] = notes
        # Update item data for the validated song
        for i in range(self.count()):
            item = self.item(i)
            if item is None:
                continue
            meta = item.data(Qt.ItemDataRole.UserRole)
            if meta and meta.get("path_str") == path_str:
                meta["status"] = status
                meta["duration"] = info.get("duration", 0)
                meta["bpm"] = info.get("bpm", 0)
                meta["note_count"] = info.get("note_count", 0)
                item.setData(Qt.ItemDataRole.UserRole, meta)
                break

    def get_song_info(self, song: Path) -> dict | None:
        """Get cached song info for a validated song."""
        return self._song_info.get(str(song))

    def get_validation_status(self, song: Path) -> str:
        """Get validation status for a song."""
        return self._validation_results.get(str(song), "pending")

    def clear_validation_cache(self) -> None:
        """Clear the validation cache (e.g., when folder changes)."""
        self._validation_cache.clear()

    def _rebuild_list(self) -> None:
        """Rebuild the list widget from filtered songs with metadata."""
        self.clear()
        for song in self._filtered_songs:
            item = QListWidgetItem(song.stem)
            # Build metadata dict
            path_str = str(song)
            status = self._validation_results.get(path_str, "pending")
            info = self._song_info.get(path_str, {})
            meta = {
                "stem": song.stem,
                "path_str": path_str,
                "status": status,
                "is_favorite": song.stem in self._favorites,
                "duration": info.get("duration", 0),
                "bpm": info.get("bpm", 0),
                "note_count": info.get("note_count", 0),
            }
            item.setData(Qt.ItemDataRole.UserRole, meta)
            self.addItem(item)

    def _on_selection_changed(self, current: QListWidgetItem | None, previous) -> None:
        """Emit song_selected when selection changes."""
        song = self.get_selected_song()
        self.song_selected.emit(song)

    def _on_double_click(self, item: QListWidgetItem) -> None:
        """Emit song_double_clicked on double-click."""
        song = self.get_selected_song()
        if song:
            self.song_double_clicked.emit(song)
