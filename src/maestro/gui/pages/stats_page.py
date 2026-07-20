"""Stats page — top songs, keys, and chords across all playback sessions."""

from __future__ import annotations

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.theme import SPACING
from maestro.gui.utils import format_time
from maestro.stats import load_stats, top_chords, top_keys, top_songs


class StatsPage(QWidget):
    """Page displaying aggregated playback statistics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        content = QWidget()
        content.setMaximumWidth(680)
        layout = QVBoxLayout(content)
        layout.setSpacing(SPACING["lg"])

        # ── Header ──
        title = QLabel("STATS")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # ── Most played songs ──
        layout.addWidget(self._make_section("Most Played Songs"))
        self._songs_label = QLabel()
        self._songs_label.setProperty("class", "caption")
        self._songs_label.setWordWrap(True)
        layout.addWidget(self._songs_label)

        # ── Most pressed keys ──
        layout.addWidget(self._make_section("Most Pressed Keys"))
        self._keys_label = QLabel()
        self._keys_label.setProperty("class", "caption")
        self._keys_label.setWordWrap(True)
        layout.addWidget(self._keys_label)

        # ── Most used chords ──
        layout.addWidget(self._make_section("Most Used Chords"))
        self._chords_label = QLabel()
        self._chords_label.setProperty("class", "caption")
        self._chords_label.setWordWrap(True)
        layout.addWidget(self._chords_label)

        # ── Summary footer ──
        layout.addWidget(self._make_section("Summary"))
        self._summary_label = QLabel()
        self._summary_label.setProperty("class", "caption")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        layout.addStretch()

        # Center the content in the scroll area
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.addStretch()
        scroll_layout.addWidget(content)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        outer.addWidget(scroll)

    @staticmethod
    def _make_section(heading: str) -> QLabel:
        label = QLabel(heading.upper())
        label.setProperty("class", "section-heading")
        return label

    def _load_and_display(self) -> None:
        stats = load_stats()

        # Songs
        songs = top_songs(stats)
        if songs:
            lines = [
                f"{i}. {name}  —  {count} play{'s' if count != 1 else ''}"
                for i, (name, count) in enumerate(songs, 1)
            ]
            self._songs_label.setText("\n".join(lines))
        else:
            self._songs_label.setText("No plays yet. Play some songs to collect stats.")

        # Keys
        keys = top_keys(stats)
        if keys:
            text = "  ".join(f"{k}: {v}" for k, v in keys)
            self._keys_label.setText(text)
        else:
            self._keys_label.setText("No keys pressed yet. Play a song to collect stats.")

        # Chords
        chords = top_chords(stats)
        if chords:
            lines = [
                f"{i}. {name}  —  {count} hit{'s' if count != 1 else ''}"
                for i, (name, count) in enumerate(chords, 1)
            ]
            self._chords_label.setText("\n".join(lines))
        else:
            self._chords_label.setText("No chords detected yet. Play some songs to collect stats.")

        # Summary
        total_time = format_time(stats.get("total_play_time_seconds", 0))
        self._summary_label.setText(
            f"Total Plays: {stats.get('total_plays', 0)}\n"
            f"Total Notes: {stats.get('total_notes_played', 0):,}\n"
            f"Total Time: {total_time}"
        )

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._load_and_display()
