"""Tests for the playback stats module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from maestro.stats import (
    _CHORD_WINDOW,
    DEFAULT_STATS,
    _detect_chords,
    _stats_path,
    chord_key_to_names,
    game_mode_stats,
    load_stats,
    midi_to_name,
    reset_stats,
    save_stats,
    top_chords,
    top_keys,
    top_notes,
    top_songs,
    update_stats,
)


@dataclass
class FakeKeyEvent:
    time: float
    action: str
    key: str
    midi_note: int = 0


# ── Helpers ──────────────────────────────────────────────────────────


def _make_events(
    *notes: tuple[float, str, int],
) -> list[FakeKeyEvent]:
    """Create a list of KeyEvent-compatible objects from ``(time, key, midi)``."""
    return [
        FakeKeyEvent(time=t, action="down", key=k, midi_note=m)
        for t, k, m in notes
    ]


# ── Path & defaults ──────────────────────────────────────────────────


def test_stats_path_is_in_maestro_dir(monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats.os.name", "posix")
    monkeypatch.setattr("maestro.stats.Path.home", lambda: Path("/home/user"))
    assert str(_stats_path()).endswith("/.maestro/stats.json")


def test_load_stats_returns_defaults_when_no_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    assert load_stats() == DEFAULT_STATS


def test_save_and_load_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    stats = dict(DEFAULT_STATS)
    stats["total_plays"] = 5
    save_stats(stats)
    loaded = load_stats()
    assert loaded["total_plays"] == 5


def test_load_stats_handles_corrupt_file(tmp_path, monkeypatch) -> None:
    p = tmp_path / "stats.json"
    p.write_text("not json")
    monkeypatch.setattr("maestro.stats._stats_path", lambda: p)
    assert load_stats() == DEFAULT_STATS


def test_load_stats_merges_missing_keys(tmp_path, monkeypatch) -> None:
    p = tmp_path / "stats.json"
    p.write_text('{"total_plays": 3}')
    monkeypatch.setattr("maestro.stats._stats_path", lambda: p)
    stats = load_stats()
    assert stats["total_plays"] == 3
    assert stats["song_plays"] == {}


# ── update_stats ─────────────────────────────────────────────────────


def test_update_increments_total_plays(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "test_song", 10.0)
    stats = load_stats()
    assert stats["total_plays"] == 1


def test_update_increments_song_plays(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "moonlight", 5.0)
    update_stats(_make_events((0.0, "b", 62)), "moonlight", 3.0)
    stats = load_stats()
    assert stats["song_plays"]["moonlight"] == 2


def test_update_increments_key_presses(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    events = _make_events((0.0, "a", 60), (1.0, "a", 60), (2.0, "s", 62))
    update_stats(events, "song", 5.0)
    stats = load_stats()
    assert stats["key_presses"]["a"] == 2
    assert stats["key_presses"]["s"] == 1


def test_update_ignores_up_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    events = [
        FakeKeyEvent(0.0, "down", "a", 60),
        FakeKeyEvent(0.5, "up", "a", 60),
    ]
    update_stats(events, "song", 5.0)
    stats = load_stats()
    assert stats["key_presses"].get("a", 0) == 1


def test_update_adds_duration(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "song", 12.5)
    update_stats(_make_events((0.0, "b", 62)), "song2", 7.5)
    stats = load_stats()
    assert stats["total_play_time_seconds"] == 20.0


def test_update_increments_total_notes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60), (1.0, "b", 62), (2.0, "c", 64)), "song", 5.0)
    stats = load_stats()
    assert stats["total_notes_played"] == 3


# ── Chord detection ──────────────────────────────────────────────────


def test_detect_three_note_chord() -> None:
    chords: dict[str, int] = {}
    events = _make_events((0.0, "a", 60), (0.01, "s", 64), (0.02, "d", 67))
    _detect_chords(events, chords)
    assert chords == {"60/64/67": 1}


def test_chord_ignores_single_note() -> None:
    chords: dict[str, int] = {}
    events = _make_events((0.0, "a", 60), (0.5, "s", 64), (1.0, "d", 67))
    _detect_chords(events, chords)
    assert chords == {}


def test_chord_sorts_notes_within_group() -> None:
    chords: dict[str, int] = {}
    events = _make_events((0.0, "a", 67), (0.01, "s", 60), (0.02, "d", 64))
    _detect_chords(events, chords)
    assert chords == {"60/64/67": 1}


def test_chord_gap_boundary() -> None:
    chords: dict[str, int] = {}
    gap = _CHORD_WINDOW + 0.01
    events = _make_events(
        (0.0, "a", 60), (0.01, "s", 64),  # chord 1
        (gap, "d", 62), (gap + 0.01, "f", 65),  # chord 2
    )
    _detect_chords(events, chords)
    assert chords == {"60/64": 1, "62/65": 1}


def test_chord_multiple_groups() -> None:
    chords: dict[str, int] = {}
    events = _make_events(
        (0.0, "a", 60), (0.01, "b", 64),
        (0.5, "c", 62), (0.51, "d", 65),
        (1.0, "e", 60), (1.01, "f", 64),  # same as first chord
    )
    _detect_chords(events, chords)
    assert chords == {"60/64": 2, "62/65": 1}


def test_chord_empty_events() -> None:
    chords: dict[str, int] = {}
    _detect_chords([], chords)
    assert chords == {}


# ── MIDI name helpers ────────────────────────────────────────────────


def test_midi_to_name_c4() -> None:
    assert midi_to_name(60) == "C4"


def test_midi_to_name_c_sharp() -> None:
    assert midi_to_name(61) == "C#4"


def test_midi_to_name_a4() -> None:
    assert midi_to_name(69) == "A4"


def test_midi_to_name_b4() -> None:
    assert midi_to_name(71) == "B4"


def test_midi_to_name_c5() -> None:
    assert midi_to_name(72) == "C5"


def test_chord_key_to_names_c_major() -> None:
    assert chord_key_to_names("60/64/67") == "C4/E4/G4"


# ── Top-N helpers ────────────────────────────────────────────────────


def test_top_songs() -> None:
    stats = dict(DEFAULT_STATS, song_plays={"a": 5, "b": 3, "c": 1})
    result = top_songs(stats, n=2)
    assert result == [("a", 5), ("b", 3)]


def test_top_keys() -> None:
    stats = dict(DEFAULT_STATS, key_presses={"x": 10, "y": 7, "z": 2})
    result = top_keys(stats, n=2)
    assert result == [("x", 10), ("y", 7)]


def test_top_chords() -> None:
    stats = dict(DEFAULT_STATS, chords={"60/64/67": 5, "62/65/69": 3})
    result = top_chords(stats, n=2)
    assert result == [("C4/E4/G4", 5), ("D4/F4/A4", 3)]


def test_top_empty() -> None:
    stats = dict(DEFAULT_STATS)
    assert top_songs(stats) == []
    assert top_keys(stats) == []
    assert top_chords(stats) == []
    assert top_notes(stats) == []


# ── Note frequency ───────────────────────────────────────────────────


def test_update_tracks_note_frequency(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    events = _make_events((0.0, "a", 60), (1.0, "b", 60), (2.0, "c", 64))
    update_stats(events, "song", 5.0)
    stats = load_stats()
    assert stats["note_frequency"]["60"] == 2
    assert stats["note_frequency"]["64"] == 1


def test_top_notes_returns_ranked_names() -> None:
    stats = dict(DEFAULT_STATS, note_frequency={"60": 10, "64": 7, "67": 3})
    result = top_notes(stats, n=2)
    assert result == [("C4", 10), ("E4", 7)]


# ── Per-game-mode ────────────────────────────────────────────────────


def test_update_tracks_game_mode(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "song", 5.0, game_mode="Heartopia")
    update_stats(_make_events((0.0, "b", 62)), "song2", 3.0, game_mode="WWM")
    stats = load_stats()
    gm = stats["by_game"]
    assert gm["Heartopia"]["total_plays"] == 1
    assert gm["Heartopia"]["total_notes_played"] == 1
    assert gm["WWM"]["total_plays"] == 1


def test_update_empty_game_mode_not_tracked(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "song", 5.0, game_mode="")
    stats = load_stats()
    assert stats["by_game"] == {}


def test_game_mode_stats_returns_dict() -> None:
    stats = dict(DEFAULT_STATS, by_game={"Heartopia": {"total_plays": 3}})
    result = game_mode_stats(stats)
    assert result["Heartopia"]["total_plays"] == 3


# ── Reset stats ──────────────────────────────────────────────────────


def test_reset_stats_clears_all_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "song", 10.0, game_mode="Heartopia")
    reset_stats()
    stats = load_stats()
    assert stats == DEFAULT_STATS


def test_reset_stats_persists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("maestro.stats._stats_path", lambda: tmp_path / "stats.json")
    update_stats(_make_events((0.0, "a", 60)), "song", 5.0)
    reset_stats()
    loaded = load_stats()
    assert loaded["total_plays"] == 0
    assert loaded["song_plays"] == {}
    assert loaded["by_game"] == {}
