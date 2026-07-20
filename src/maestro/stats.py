"""Playback statistics — track most-played songs, keys, and chords across sessions.

Stats are persisted to ``~/.maestro/stats.json`` and updated after each
completed playback by ``Player._export_played_notes()``.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

_STATS_FILENAME = "stats.json"

_CHORD_WINDOW = 0.05  # seconds — notes within this window are grouped as a chord
_TOP_N = 10  # how many entries to show in each category


def _stats_path() -> Path:
    """Return the path to the stats JSON file."""
    if os.name == "nt":
        base = os.environ.get("APPDATA", "")
    else:
        base = os.path.join(Path.home(), ".maestro")
    return Path(base) / _STATS_FILENAME


def _empty_game_stats() -> dict[str, Any]:
    """Return a fresh per-game-mode stats sub-dict."""
    return {
        "total_plays": 0,
        "total_notes_played": 0,
        "total_play_time_seconds": 0.0,
    }


DEFAULT_STATS: dict[str, Any] = {
    "total_plays": 0,
    "total_notes_played": 0,
    "total_play_time_seconds": 0.0,
    "song_plays": {},
    "key_presses": {},
    "note_frequency": {},
    "chords": {},
    "by_game": {},
}


def load_stats() -> dict[str, Any]:
    """Read stats from disk, falling back to defaults for missing keys."""
    path = _stats_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_STATS)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULT_STATS)

    merged = copy.deepcopy(DEFAULT_STATS)
    for key in DEFAULT_STATS:
        if key in raw and isinstance(raw[key], type(DEFAULT_STATS[key])):
            merged[key] = raw[key]

    return merged


def save_stats(stats: dict[str, Any]) -> None:
    """Atomically write stats to disk."""
    path = _stats_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(stats, indent=2, ensure_ascii=False)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, payload.encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp, path)


def update_stats(
    events: list[Any],
    song_name: str,
    duration: float,
    game_mode: str = "",
) -> None:
    """Increment counters and detect chords from a finished playback.

    ``events`` is a list of ``KeyEvent`` objects with attributes
    ``time``, ``action``, ``key``, and ``midi_note``.
    """
    stats = load_stats()

    stats["total_plays"] += 1
    stats["total_play_time_seconds"] += duration

    songs: dict[str, int] = stats["song_plays"]
    songs[song_name] = songs.get(song_name, 0) + 1

    keys: dict[str, int] = stats["key_presses"]
    notes: dict[str, int] = stats["note_frequency"]

    down_events = [e for e in events if e.action == "down"]
    stats["total_notes_played"] += len(down_events)

    for evt in down_events:
        keys[evt.key] = keys.get(evt.key, 0) + 1
        midi = evt.midi_note
        notes[str(midi)] = notes.get(str(midi), 0) + 1

    _detect_chords(down_events, stats["chords"])

    # Per-game-mode breakdown
    if game_mode and game_mode.strip():
        by_game: dict[str, dict[str, Any]] = stats["by_game"]
        gs = by_game.setdefault(game_mode, _empty_game_stats())
        gs["total_plays"] += 1
        gs["total_notes_played"] += len(down_events)
        gs["total_play_time_seconds"] += duration

    save_stats(stats)


def _detect_chords(events: list[Any], chords: dict[str, int]) -> None:
    """Walk through time-sorted down-events and group concurrent notes into chords.

    Two events belong to the same chord by being within ``_CHORD_WINDOW``
    seconds of the chord group's first event.
    """
    if not events:
        return

    sorted_events = sorted(events, key=lambda e: e.time)

    i = 0
    n = len(sorted_events)
    while i < n:
        group_start = sorted_events[i].time
        group: list[int] = [sorted_events[i].midi_note]
        i += 1
        while i < n and (sorted_events[i].time - group_start) <= _CHORD_WINDOW:
            group.append(sorted_events[i].midi_note)
            i += 1

        if len(group) >= 2:
            group.sort()
            chord_key = "/".join(str(m) for m in group)
            chords[chord_key] = chords.get(chord_key, 0) + 1


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_name(midi: int) -> str:
    """Convert a MIDI note number to a human-readable name (e.g. 60 -> "C4")."""
    octave = midi // 12 - 1
    note = _NOTE_NAMES[midi % 12]
    return f"{note}{octave}"


def chord_key_to_names(chord_key: str) -> str:
    """Convert a chord key like ``"60/64/67"`` to ``"C4/E4/G4"``."""
    return "/".join(midi_to_name(int(m)) for m in chord_key.split("/"))


def top_songs(stats: dict[str, Any], n: int = _TOP_N) -> list[tuple[str, int]]:
    """Return the top *n* most-played songs as ``(name, count)``."""
    items = sorted(stats["song_plays"].items(), key=lambda x: x[1], reverse=True)
    return items[:n]


def top_keys(stats: dict[str, Any], n: int = _TOP_N) -> list[tuple[str, int]]:
    """Return the top *n* most-pressed keyboard keys."""
    items = sorted(stats["key_presses"].items(), key=lambda x: x[1], reverse=True)
    return items[:n]


def top_notes(stats: dict[str, Any], n: int = _TOP_N) -> list[tuple[str, int]]:
    """Return the top *n* most-played musical notes as ``(note_name, count)``."""
    freq: dict[str, int] = stats.get("note_frequency", {})
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [(midi_to_name(int(k)), v) for k, v in items[:n]]


def top_chords(stats: dict[str, Any], n: int = _TOP_N) -> list[tuple[str, int]]:
    """Return the top *n* most-used chords as ``(note_names, count)``."""
    items = sorted(stats["chords"].items(), key=lambda x: x[1], reverse=True)
    return [(chord_key_to_names(k), v) for k, v in items[:n]]


def game_mode_stats(stats: dict[str, Any]) -> dict[str, Any]:
    """Return the per-game-mode breakdown as ``{mode: {total_plays, ...}}``."""
    result: dict[str, Any] = stats.get("by_game", {})
    return result


def reset_stats() -> None:
    """Wipe all stats and write fresh defaults to disk."""
    save_stats(copy.deepcopy(DEFAULT_STATS))
