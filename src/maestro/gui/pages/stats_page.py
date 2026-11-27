# SPDX-License-Identifier: MPL-2.0
"""Personal playback recap, built entirely from the local statistics file."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QShowEvent, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.note_keyboard import NoteKeyboard
from maestro.gui.theme import COLORS
from maestro.gui.utils import format_time
from maestro.stats import chord_key_to_names, load_stats, reset_stats, top_keys, top_songs


def label(text: str, role: str = "caption") -> QLabel:
    item = QLabel(text)
    item.setTextFormat(Qt.TextFormat.PlainText)
    item.setProperty("class", role)
    item.setWordWrap(True)
    return item


def card(title: str) -> tuple[QWidget, QVBoxLayout]:
    box = QWidget()
    box.setProperty("class", "surface-card")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(16, 12, 16, 14)
    layout.setSpacing(8)
    layout.addWidget(label(title, "section-heading"))
    return box, layout


def ranked_bars(rows: list[tuple[str, int]], unit: str) -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    highest = max((value for _, value in rows), default=0)
    for name, value in rows:
        line = QHBoxLayout()
        line.addWidget(label(name), 1)
        line.addWidget(label(f"{value:,} {unit if value != 1 else unit.rstrip('s')}"))
        layout.addLayout(line)
        bar = QProgressBar()
        bar.setTextVisible(False)
        bar.setAccessibleName(f"{name}: {value:,} {unit}")
        bar.setRange(0, 1000)
        bar.setValue(round(1000 * value / highest) if highest else 0)
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"QProgressBar {{ background: {COLORS['surface2']}; border: 0; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background: {COLORS['accent']}; border-radius: 3px; }}"
        )
        layout.addWidget(bar)
    return box


def duration(seconds: float) -> str:
    minutes = int(seconds) // 60
    if minutes >= 60:
        return f"{minutes // 60}h {minutes % 60}m"
    return f"{minutes}m {int(seconds) % 60}s" if minutes else f"{int(seconds)}s"


class StatsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.scroll_area)

    def _load_and_display(self) -> None:
        stats = load_stats()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("Playback stats", "title"), 1)
        reset = QPushButton("Reset stats")
        reset.setProperty("class", "ghost")
        reset.clicked.connect(self._on_reset_clicked)
        header.addWidget(reset)
        layout.addLayout(header)

        summary = QHBoxLayout()
        for title, value in (
            ("Distinct songs", f"{len(stats['song_plays']):,}"),
            ("Play time", duration(stats["total_play_time_seconds"])),
            ("Notes played", f"{stats['total_notes_played']:,}"),
        ):
            box, body = card(title)
            body.addWidget(label(value, "title"))
            summary.addWidget(box, 1)
        layout.addLayout(summary)

        songs = top_songs(stats, 5)
        box, body = card("On repeat")
        if songs:
            body.addWidget(ranked_bars(songs, "plays"))
            total = stats["total_plays"]
            if total:
                body.addWidget(
                    label(
                        f"{songs[0][0]} accounts for {songs[0][1] / total:.0%} of your {total:,} plays."
                    )
                )
        else:
            body.addWidget(label("Play a song to start your personal recap."))
        layout.addWidget(box)

        if stats["total_plays"]:
            layout.addWidget(self._keyboard(stats))
            layout.addWidget(self._games(stats))
            layout.addWidget(self._peak(stats))
            layout.addWidget(self._history(stats))
        layout.addStretch()
        self.scroll_area.setWidget(content)

    def _keyboard(self, stats: dict[str, Any]) -> QWidget:
        box, body = card("Your piano")
        picker = QComboBox()
        picker.setAccessibleName("Keyboard view")
        picker.addItems(["Piano notes", "Game keys", "Signature chord"])
        body.addWidget(picker, alignment=Qt.AlignmentFlag.AlignLeft)
        stack = QStackedWidget()
        # Only the selected view should determine the card height.
        notes = {
            int(k): v
            for k, v in stats["note_frequency"].items()
            if k.isdigit() and 0 <= int(k) <= 127 and v > 0
        }
        stack.addWidget(NoteKeyboard(notes) if notes else label("No notes recorded yet."))
        keys = top_keys(stats)
        stack.addWidget(ranked_bars(keys, "hits") if keys else label("No game keys recorded yet."))
        chords = stats["chords"]
        if chords:
            chord = max(chords, key=chords.__getitem__)
            pane = QWidget()
            inner = QVBoxLayout(pane)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(label(f"{chord_key_to_names(chord)}  ·  {chords[chord]:,} appearances"))
            inner.addWidget(NoteKeyboard({int(note): chords[chord] for note in chord.split("/")}))
            stack.addWidget(pane)
        else:
            stack.addWidget(
                label("Play a passage with simultaneous notes to see your signature chord.")
            )

        def switch(index: int) -> None:
            for i in range(stack.count()):
                policy = QSizePolicy.Policy.Preferred if i == index else QSizePolicy.Policy.Ignored
                page = stack.widget(i)
                if page is not None:
                    page.setSizePolicy(QSizePolicy.Policy.Preferred, policy)
            stack.setCurrentIndex(index)
            stack.updateGeometry()

        picker.currentIndexChanged.connect(switch)
        switch(0)
        body.addWidget(stack)
        return box

    def _games(self, stats: dict[str, Any]) -> QWidget:
        box, body = card("By game")
        picker = QComboBox()
        picker.setAccessibleName("Game comparison metric")
        picker.addItems(["Time", "Plays", "Notes"])
        body.addWidget(picker, alignment=Qt.AlignmentFlag.AlignLeft)
        stack = QStackedWidget()
        colors = ["accent", "green", "red", "yellow", "overlay"]
        for metric in ("total_play_time_seconds", "total_plays", "total_notes_played"):
            pane = QWidget()
            inner = QVBoxLayout(pane)
            inner.setContentsMargins(0, 0, 0, 0)
            strip = QHBoxLayout()
            strip.setSpacing(1)
            inner.addLayout(strip)
            values = {
                name: game[metric]
                for name, game in stats["by_game"].items()
                if game.get(metric, 0) > 0
            }
            missing = stats[metric] - sum(values.values())
            if missing > (0.001 if metric == "total_play_time_seconds" else 0):
                values["Unspecified"] = missing
            total = sum(values.values())
            for i, (name, value) in enumerate(sorted(values.items(), key=lambda item: -item[1])):
                color = COLORS[colors[i % len(colors)]]
                part = QFrame()
                part.setFixedHeight(12)
                part.setStyleSheet(f"background-color: {color};")
                amount = duration(value) if metric == "total_play_time_seconds" else f"{value:,}"
                desc = f"{name.replace('_', ' ').title()}   ·   {amount}   ·   {value / total:.0%}"
                part.setToolTip(desc)
                strip.addWidget(part, max(1, round(1000 * value / total)))
                row = QHBoxLayout()
                dot = QFrame()
                dot.setFixedSize(9, 9)
                dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
                row.addWidget(dot)
                row.addWidget(label(desc), 1)
                inner.addLayout(row)
            if not values:
                inner.addWidget(label("No activity recorded for this measure yet."))
            inner.addStretch()
            stack.addWidget(pane)
        picker.currentIndexChanged.connect(stack.setCurrentIndex)
        body.addWidget(stack)
        return box

    def _peak(self, stats: dict[str, Any]) -> QWidget:
        box, body = card("Busiest five seconds")
        peak = stats["peak_passage"]
        if peak:
            body.addWidget(label(f"{peak['count']:,} notes  ·  {peak['song']}", "title"))
            toggle = QPushButton(f"Passage at {format_time(peak['start'])}")
            toggle.setCheckable(True)
            body.addWidget(toggle, alignment=Qt.AlignmentFlag.AlignLeft)
            bars = ranked_bars(
                [(f"Second {i + 1}", n) for i, n in enumerate(peak["bins"])], "notes"
            )
            bars.hide()
            toggle.toggled.connect(bars.setVisible)
            body.addWidget(bars)
        else:
            body.addWidget(label("Your next playback with notes will set your first record."))
        return box

    def _history(self, stats: dict[str, Any]) -> QWidget:
        box, body = card("Playback history")
        daily = stats["daily_plays"]
        if not daily:
            body.addWidget(label("Dated history begins with your next playback."))
            return box
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        weeks = []
        for offset in reversed(range(4)):
            start = monday - timedelta(weeks=offset)
            if (start + timedelta(days=6)).isoformat() < min(daily):
                continue
            count = sum(daily.get((start + timedelta(days=i)).isoformat(), 0) for i in range(7))
            weeks.append(("This week" if offset == 0 else f"Week of {start:%b %d}", count))
        body.addWidget(ranked_bars(weeks, "plays"))
        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setMaximumDate(QDate.currentDate())
        calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        highest = max(daily.values())
        for day, count in daily.items():
            style = QTextCharFormat()
            ink = QColor(COLORS["accent"])
            ink.setAlphaF(0.18 + 0.52 * count / highest)
            style.setBackground(ink)
            style.setForeground(QColor(COLORS["text"]))
            calendar.setDateTextFormat(QDate.fromString(day, "yyyy-MM-dd"), style)
        body.addWidget(calendar)
        selected = label("")

        def show_day() -> None:
            day = calendar.selectedDate()
            count = daily.get(day.toString("yyyy-MM-dd"), 0)
            selected.setText(f"{day.toString('d MMMM yyyy')} · {count:,} recorded plays")

        calendar.selectionChanged.connect(show_day)
        show_day()
        body.addWidget(selected)
        return box

    def _on_reset_clicked(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Reset stats",
            "Clear all local playback statistics? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            reset_stats()
            self._load_and_display()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._load_and_display()
