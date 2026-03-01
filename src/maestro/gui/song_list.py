"""Song list widget with custom delegate for rich two-line song items."""

from pathlib import Path

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from maestro.gui.theme import COLORS, FONT
from maestro.gui.utils import get_songs_from_folder


class SongItemDelegate(QStyledItemDelegate):
    """Custom delegate for painting rich two-line song items.

    Each item displays:
      - Left accent bar (3px, color-coded by validation status)
      - Favorite star (vertically centered)
      - Line 1: Song name left-aligned, duration right-aligned
      - Line 2: BPM · note count (valid) | status text (pending/invalid)
    """

    # Layout grid — all values intentional, most multiples of 4
    _ITEM_H = 68
    _BAR_W = 3
    _STAR_X = 10
    _STAR_W = 24
    _CONTENT_X = 38
    _PAD_R = 12
    _LINE1_Y = 8
    _LINE1_H = 28
    _LINE2_Y = 36
    _LINE2_H = 24

    def sizeHint(  # noqa: N802
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        return QSize(option.rect.width(), self._ITEM_H)

    def paint(  # noqa: N802
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = option.rect
        meta = index.data(Qt.ItemDataRole.UserRole)
        if meta is None:
            meta = {
                "stem": index.data() or "",
                "status": "pending",
                "is_favorite": False,
                "duration": 0,
                "bpm": 0,
                "note_count": 0,
            }
        status = meta.get("status", "pending")

        # ── Background ────────────────────────────────────────────────
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if is_selected:
            painter.fillRect(r, QColor(COLORS["surface_hover"]))
        elif is_hovered:
            painter.fillRect(r, QColor(COLORS["surface2"]))

        # ── Left accent bar ───────────────────────────────────────────
        bar_color = {
            "valid": COLORS["green_dark"],
            "invalid": COLORS["red_dark"],
        }.get(status, COLORS["pending"])
        painter.fillRect(r.x(), r.y(), self._BAR_W, r.height(), QColor(bar_color))

        # ── Favorite star (vertically centered in full item) ──────────
        star_font = QFont()
        star_font.setPointSize(FONT["body"]["size"] + 2)
        painter.setFont(star_font)
        star_rect = QRect(r.x() + self._STAR_X, r.y(), self._STAR_W, r.height())
        if meta.get("is_favorite"):
            painter.setPen(QColor(COLORS["yellow"]))
            painter.drawText(star_rect, Qt.AlignmentFlag.AlignVCenter, "\u2605")
        else:
            painter.setPen(QColor(COLORS["pending"]))
            painter.drawText(star_rect, Qt.AlignmentFlag.AlignVCenter, "\u2606")

        # ── Content area ──────────────────────────────────────────────
        cx = r.x() + self._CONTENT_X
        cw = r.width() - self._CONTENT_X - self._PAD_R

        # -- Line 1: song name + duration --
        name_font = QFont()
        name_font.setPointSize(FONT["body"]["size"])
        painter.setFont(name_font)

        # Measure duration to reserve right-side space
        dur_text = ""
        dur_w = 0
        duration = meta.get("duration", 0)
        if duration > 0 and status == "valid":
            m = int(duration // 60)
            s = int(duration % 60)
            dur_text = f"{m}:{s:02d}"
            dur_w = painter.fontMetrics().horizontalAdvance(dur_text) + 12

        # Song name (left, elided to fit)
        name_w = cw - dur_w
        elided = painter.fontMetrics().elidedText(
            meta["stem"],
            Qt.TextElideMode.ElideRight,
            name_w,
        )
        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(
            QRect(cx, r.y() + self._LINE1_Y, name_w, self._LINE1_H),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided,
        )

        # Duration (right-aligned, readable but not dominant)
        if dur_text:
            painter.setPen(QColor(COLORS["text_dim"]))
            painter.drawText(
                QRect(cx + name_w, r.y() + self._LINE1_Y, dur_w, self._LINE1_H),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                dur_text,
            )

        # -- Line 2: metadata or status text --
        caption_font = QFont()
        caption_font.setPointSize(FONT["caption"]["size"])
        painter.setFont(caption_font)
        line2 = QRect(cx, r.y() + self._LINE2_Y, cw, self._LINE2_H)

        if status == "pending":
            painter.setPen(QColor(COLORS["subtext"]))
            painter.drawText(line2, Qt.AlignmentFlag.AlignVCenter, "Validating\u2026")
        elif status == "invalid":
            painter.setPen(QColor(COLORS["red"]))
            painter.drawText(
                line2,
                Qt.AlignmentFlag.AlignVCenter,
                "Invalid MIDI file",
            )
        else:
            parts: list[str] = []
            bpm = meta.get("bpm", 0)
            note_count = meta.get("note_count", 0)
            if bpm > 0:
                parts.append(f"{bpm} BPM")
            if note_count > 0:
                parts.append(f"{note_count} notes")
            playable = meta.get("playable", 0)
            total = meta.get("total", 0)
            if total > 0:
                pct = round(playable / total * 100)
                parts.append(f"{playable}/{total} playable ({pct}%)")
            if parts:
                painter.setPen(QColor(COLORS["subtext"]))
                painter.drawText(
                    line2,
                    Qt.AlignmentFlag.AlignVCenter,
                    " \u00b7 ".join(parts),
                )

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
        self._song_compatibility: dict[str, tuple[int, int]] = {}
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
                # Touch display role to trigger delegate repaint
                item.setText(meta["stem"])
                break

    def update_song_compatibility(self, path_str: str, playable: int, total: int) -> None:
        """Update compatibility info for a song and repaint its item."""
        self._song_compatibility[path_str] = (playable, total)
        for i in range(self.count()):
            item = self.item(i)
            if item is None:
                continue
            meta = item.data(Qt.ItemDataRole.UserRole)
            if meta and meta.get("path_str") == path_str:
                meta["playable"] = playable
                meta["total"] = total
                item.setData(Qt.ItemDataRole.UserRole, meta)
                item.setText(meta["stem"])
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
            compat = self._song_compatibility.get(path_str, (0, 0))
            meta = {
                "stem": song.stem,
                "path_str": path_str,
                "status": status,
                "is_favorite": song.stem in self._favorites,
                "duration": info.get("duration", 0),
                "bpm": info.get("bpm", 0),
                "note_count": info.get("note_count", 0),
                "playable": compat[0],
                "total": compat[1],
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
