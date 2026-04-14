"""Tests for NowPlayingPanel."""
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from maestro.gui.progress_panel import NowPlayingPanel


@pytest.fixture
def song_file(tmp_path):
    """A real on-disk MIDI file so Path.stat() works."""
    p = tmp_path / "test_song.mid"
    p.write_bytes(b"x" * 2048)  # 2 KB
    return p


def test_fresh_panel_shows_no_song_loaded(qtbot):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    assert panel._song_label.text() == "No song loaded"
    assert not panel._meta_widget.isVisible()
    assert not panel._status_label.isVisible()


def test_valid_song_populates_grid(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()  # required so isVisible() queries return True
    info = {"duration": 120.0, "bpm": 120, "note_count": 456}
    panel.update_metadata(song_file, "valid", info, (400, 456))
    assert panel._song_label.text() == song_file.stem
    assert panel._bpm_value.text() == "120"
    assert panel._notes_value.text() == "456 (400 playable \u00b7 88%)"
    assert panel._size_value.text() == "2.0 KB"
    expected_date = datetime.fromtimestamp(song_file.stat().st_mtime).strftime("%Y-%m-%d")
    assert panel._modified_value.text() == expected_date
    assert panel._meta_widget.isVisible()
    assert not panel._status_label.isVisible()


def test_valid_song_with_zero_total_hides_playable_suffix(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()
    info = {"duration": 120.0, "bpm": 120, "note_count": 456}
    panel.update_metadata(song_file, "valid", info, (0, 0))
    assert panel._notes_value.text() == "456"  # no suffix


def test_pending_song_shows_validating_label(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.update_metadata(song_file, "pending", None, (0, 0))
    assert panel._status_label.text() == "Validating\u2026"
    assert panel._status_label.isVisible()
    assert not panel._meta_widget.isVisible()


def test_invalid_song_shows_invalid_label(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.update_metadata(song_file, "invalid", None, (0, 0))
    assert panel._status_label.text() == "Invalid MIDI file"
    assert panel._status_label.isVisible()
    assert not panel._meta_widget.isVisible()


def test_update_metadata_with_none_song_resets(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()
    info = {"duration": 120.0, "bpm": 120, "note_count": 10}
    panel.update_metadata(song_file, "valid", info, (10, 10))
    assert panel._meta_widget.isVisible()
    panel.update_metadata(None, "", None, (0, 0))
    assert panel._song_label.text() == "No song loaded"
    assert not panel._meta_widget.isVisible()
    assert not panel._status_label.isVisible()


def test_stat_failure_renders_em_dash(qtbot, song_file):
    panel = NowPlayingPanel()
    qtbot.addWidget(panel)
    panel.show()
    info = {"duration": 120.0, "bpm": 120, "note_count": 10}
    with patch.object(Path, "stat", side_effect=OSError("deleted")):
        panel.update_metadata(song_file, "valid", info, (10, 10))
    assert panel._size_value.text() == "\u2014"
    assert panel._modified_value.text() == "\u2014"
    # BPM + Notes still populate normally
    assert panel._bpm_value.text() == "120"
    assert panel._notes_value.text() == "10 (10 playable \u00b7 100%)"
