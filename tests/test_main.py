import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from maestro.main import Maestro


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('maestro.main.Player') as player_mock, \
         patch('maestro.main.SongPicker') as picker_mock, \
         patch('maestro.main.keyboard') as kb_mock:
        yield {
            'player': player_mock.return_value,
            'picker': picker_mock.return_value,
            'keyboard': kb_mock,
        }


def test_maestro_initializes(mock_dependencies, tmp_path):
    """Maestro should initialize with songs folder."""
    app = Maestro(songs_folder=tmp_path)
    assert app.songs_folder == tmp_path


def test_maestro_toggle_pause(mock_dependencies, tmp_path):
    """Toggle pause should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.toggle_pause()
    mock_dependencies['player'].toggle_pause.assert_called_once()


def test_maestro_stop(mock_dependencies, tmp_path):
    """Stop should delegate to player."""
    app = Maestro(songs_folder=tmp_path)
    app.stop()
    mock_dependencies['player'].stop.assert_called_once()
