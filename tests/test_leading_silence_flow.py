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


def test_refresh_click_prompts_process_dialog(window, tmp_path):
    """Refresh button triggers validation, then shows the process-silence
    dialog. On accept, auto-process runs."""
    _seed_song_notes(window, tmp_path, {"offender.mid": 2.0})

    with patch.object(window, "_refresh_songs") as mock_refresh:
        window._on_refresh_click()
    assert window._refresh_auto_trim is True
    mock_refresh.assert_called_once()

    # Validation finishes -> dialog shown with include_trailing=True.
    with (
        patch("maestro.gui.main_window.LeadingSilenceDialog") as dialog_cls,
        patch.object(window, "_auto_process_all") as mock_auto,
    ):
        dialog_cls.return_value.exec.return_value = 1  # Accept
        window._on_validation_finished()

    dialog_cls.assert_called_once()
    assert dialog_cls.call_args.kwargs.get("include_trailing") is True
    mock_auto.assert_called_once()
    assert window._refresh_auto_trim is False


def test_refresh_click_skip_does_not_process(window, tmp_path):
    """If user skips the process-silence dialog, no processing happens."""
    _seed_song_notes(window, tmp_path, {"offender.mid": 2.0})
    window._refresh_auto_trim = True

    with (
        patch("maestro.gui.main_window.LeadingSilenceDialog") as dialog_cls,
        patch.object(window, "_auto_process_all") as mock_auto,
    ):
        dialog_cls.return_value.exec.return_value = 0  # Skip
        window._on_validation_finished()

    dialog_cls.assert_called_once()
    mock_auto.assert_not_called()


def test_auto_process_normalizes_and_trims(window, tmp_path):
    """Auto-process runs leading trim for offenders and trailing normalize
    for every song — then refreshes the list once if anything changed."""
    _seed_song_notes(window, tmp_path, {
        "offender.mid": 2.0,
        "clean.mid": 0.1,
    })
    offender_path = tmp_path / "offender.mid"
    clean_path = tmp_path / "clean.mid"
    window._dashboard._song_list._songs = [offender_path, clean_path]

    with (
        patch("maestro.gui.main_window.trim_leading_silence") as mock_trim,
        patch(
            "maestro.gui.main_window.normalize_trailing_silence",
            return_value=True,
        ) as mock_norm,
        patch.object(window, "_refresh_songs") as mock_refresh,
    ):
        window._auto_process_all()

    # Leading trim runs only for the offender.
    mock_trim.assert_called_once_with(offender_path)
    # Trailing normalize runs for every song.
    assert mock_norm.call_count == 2
    mock_refresh.assert_called_once()


def test_initial_validation_still_prompts_dialog(window, tmp_path):
    """Without the refresh flag, validation completion still uses the dialog
    path (initial-load / folder-change behaviour unchanged)."""
    _seed_song_notes(window, tmp_path, {"offender.mid": 2.0})
    assert window._refresh_auto_trim is False

    with patch("maestro.gui.main_window.LeadingSilenceDialog") as dialog_cls:
        dialog_cls.return_value.exec.return_value = 0
        window._on_validation_finished()
    dialog_cls.assert_called_once()
