"""Integration tests for the song info panel wiring on MainWindow."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maestro.gui.main_window import MainWindow


_BASE_CONFIG: dict = {
    "last_songs_folder": "",
    "game_mode": "Heartopia",
    "speed": 1.0,
    "preview_lookahead": 5,
    "transpose": False,
    "show_preview": False,
    "key_layout": "22-key (Full)",
    "wwm_key_layout": "36-key (Full)",
    "sharp_handling": "skip",
    "favorites": [],
    "recently_played": [],
    "play_key": "f2",
    "stop_key": "f3",
    "emergency_stop_key": "escape",
    "theme": "dark",
    "disclaimer_accepted": True,
    "start_fullscreen": False,
    "check_updates_on_launch": False,
    "auto_minimize_on_play": True,
    "countdown_delay": 3,
}


@pytest.fixture
def song_a(tmp_path):
    p = tmp_path / "song_a.mid"
    p.write_bytes(b"x" * 1024)
    return p


@pytest.fixture
def song_b(tmp_path):
    p = tmp_path / "song_b.mid"
    p.write_bytes(b"y" * 1024)
    return p


@pytest.fixture
def window(qtbot, tmp_path):
    """Build a MainWindow with heavy dependencies patched out.

    MainWindow takes (songs_folder, config) and internally spins up
    ValidationWorker + UpdateCheckWorker threads; we stub those to keep
    tests fast and deterministic.

    Also bypasses MainWindow.closeEvent (which shows a modal ExitDialog)
    so pytest-qt teardown doesn't hang.
    """
    with (
        patch("maestro.gui.main_window.ValidationWorker"),
        patch("maestro.gui.main_window.UpdateCheckWorker"),
    ):
        w = MainWindow(songs_folder=tmp_path, config=_BASE_CONFIG)
    w.closeEvent = lambda event: event.accept()  # type: ignore[method-assign]
    qtbot.addWidget(w)
    w._prev_state = "Stopped"
    return w


def _select_song(window, song: Path) -> None:
    """Helper: pretend the user clicked ``song`` in the song list."""
    sl = window._dashboard._song_list
    sl.get_selected_song = MagicMock(return_value=song)
    window._on_song_select(song)


def test_pending_then_valid_refreshes_panel(window, song_a):
    window._dashboard._song_list._songs = [song_a]
    window._validation_results[str(song_a)] = "pending"
    _select_song(window, song_a)
    assert window._dashboard._now_playing._status_label.text() == "Validating\u2026"

    info = {"duration": 10.0, "bpm": 100, "note_count": 42}
    window._validation_results[str(song_a)] = "valid"
    window._song_info[str(song_a)] = info
    window._on_song_validated(str(song_a), "valid", info, [], 42, 42)

    panel = window._dashboard._now_playing
    assert not panel._status_label.isVisible() or panel._status_label.text() != "Validating\u2026"
    assert panel._bpm_value.text() == "100"


def test_compat_result_refreshes_notes_row(window, song_a):
    info = {"duration": 10.0, "bpm": 100, "note_count": 456}
    window._validation_results[str(song_a)] = "valid"
    window._song_info[str(song_a)] = info
    _select_song(window, song_a)
    panel = window._dashboard._now_playing
    assert panel._notes_value.text() == "456"  # no suffix yet

    window._on_note_compatibility_result(400, 456)
    assert panel._notes_value.text() == "456 (400 playable \u00b7 88%)"


def test_other_song_updates_do_not_affect_panel(window, song_a, song_b):
    window._dashboard._song_list._songs = [song_a, song_b]
    info_a = {"duration": 10.0, "bpm": 100, "note_count": 10}
    window._validation_results[str(song_a)] = "valid"
    window._song_info[str(song_a)] = info_a
    _select_song(window, song_a)
    panel = window._dashboard._now_playing
    name_before = panel._song_label.text()
    bpm_before = panel._bpm_value.text()

    # Validation arrives for song B (not selected) — panel must not change.
    info_b = {"duration": 99.0, "bpm": 200, "note_count": 999}
    window._on_song_validated(str(song_b), "valid", info_b, [], 999, 999)
    assert panel._song_label.text() == name_before
    assert panel._bpm_value.text() == bpm_before


def test_stale_validation_result_is_dropped(window, song_a, song_b):
    """Validation result for a path not in the current song list is ignored.

    Simulates a stale worker emitting after a folder change: song_b is NOT
    in the current song list, so its validation result must not leak into
    _validation_results / _song_info.
    """
    window._dashboard._song_list._songs = [song_a]  # only song_a is current
    info_b = {"duration": 99.0, "bpm": 200, "note_count": 999}

    window._on_song_validated(str(song_b), "valid", info_b, [], 999, 999)

    assert str(song_b) not in window._validation_results
    assert str(song_b) not in window._song_info
    assert str(song_b) not in window._song_notes


def test_panel_locked_during_playback(window, song_a, song_b):
    info_a = {"duration": 10.0, "bpm": 100, "note_count": 10}
    window._validation_results[str(song_a)] = "valid"
    window._song_info[str(song_a)] = info_a
    _select_song(window, song_a)
    panel = window._dashboard._now_playing
    assert panel._song_label.text().replace("\u200b", "") == song_a.stem

    # Playback starts — state leaves "Stopped".
    window._prev_state = "Playing"

    # User clicks song B during playback.
    info_b = {"duration": 99.0, "bpm": 200, "note_count": 999}
    window._validation_results[str(song_b)] = "valid"
    window._song_info[str(song_b)] = info_b
    _select_song(window, song_b)

    # Panel still shows song A, unchanged.
    assert panel._song_label.text().replace("\u200b", "") == song_a.stem
    assert panel._bpm_value.text() == "100"
