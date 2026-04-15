"""Integration tests for leading-silence detection and trim flow."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from maestro.gui.main_window import MainWindow
from maestro.parser import Note


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
def window(qtbot, tmp_path):
    """MainWindow with heavy deps patched and closeEvent bypassed."""
    with (
        patch("maestro.gui.main_window.ValidationWorker"),
        patch("maestro.gui.main_window.UpdateCheckWorker"),
    ):
        w = MainWindow(songs_folder=tmp_path, config=_BASE_CONFIG)
    w.closeEvent = lambda event: event.accept()  # type: ignore[method-assign]
    qtbot.addWidget(w)
    return w


def _seed_song_notes(window, tmp_path: Path, first_note_times: dict[str, float]) -> None:
    """Create dummy MIDI files and seed window._song_notes with fake notes.

    Each entry in first_note_times maps filename -> first-note time (seconds).
    """
    for name, t in first_note_times.items():
        p = tmp_path / name
        p.write_bytes(b"x" * 128)
        notes = [Note(midi_note=60, time=t, duration=0.5)]
        window._song_notes[str(p)] = notes


def test_dialog_shown_when_offenders_exist(window, tmp_path):
    _seed_song_notes(window, tmp_path, {
        "offender.mid": 2.0,
        "clean.mid": 0.1,
    })
    with patch(
        "maestro.gui.main_window.LeadingSilenceDialog"
    ) as dialog_cls:
        dialog_cls.return_value.exec.return_value = 0  # Skip
        window._on_validation_finished()
    dialog_cls.assert_called_once()
    # First positional arg is the count
    assert dialog_cls.call_args.args[0] == 1


def test_dialog_not_shown_when_no_offenders(window, tmp_path):
    _seed_song_notes(window, tmp_path, {
        "clean1.mid": 0.1,
        "clean2.mid": 0.3,  # below 0.5s threshold
    })
    with patch(
        "maestro.gui.main_window.LeadingSilenceDialog"
    ) as dialog_cls:
        window._on_validation_finished()
    dialog_cls.assert_not_called()


def test_skip_flag_prevents_reprompt(window, tmp_path):
    _seed_song_notes(window, tmp_path, {"offender.mid": 2.0})
    window._silence_dialog_skipped = True
    with patch(
        "maestro.gui.main_window.LeadingSilenceDialog"
    ) as dialog_cls:
        window._on_validation_finished()
    dialog_cls.assert_not_called()


def test_trim_all_wires_through_to_refresh_songs(window, tmp_path):
    _seed_song_notes(window, tmp_path, {"offender.mid": 2.0})
    offender_path = tmp_path / "offender.mid"
    with (
        patch("maestro.gui.main_window.trim_leading_silence") as mock_trim,
        patch.object(window, "_refresh_songs") as mock_refresh,
    ):
        window._trim_all([offender_path])
    mock_trim.assert_called_once_with(offender_path)
    mock_refresh.assert_called_once()
