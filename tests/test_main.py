import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from maestro.main import Maestro


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('maestro.main.Player') as player_mock, \
         patch('maestro.main.SongPicker') as picker_mock, \
         patch('maestro.main.keyboard') as kb_mock, \
         patch('maestro.main.load_config') as load_config_mock, \
         patch('maestro.main.save_config') as save_config_mock, \
         patch('maestro.main.setup_logger') as logger_mock:
        load_config_mock.return_value = {
            'last_songs_folder': '',
            'game_mode': 'Heartopia',
            'speed': 1.0,
            'preview_lookahead': 5,
        }
        yield {
            'player': player_mock.return_value,
            'picker': picker_mock.return_value,
            'keyboard': kb_mock,
            'load_config': load_config_mock,
            'save_config': save_config_mock,
            'logger': logger_mock.return_value,
        }


def test_maestro_initializes(mock_dependencies, tmp_path):
    """Maestro should initialize with songs folder."""
    app = Maestro(songs_folder=tmp_path)
    assert app.songs_folder == tmp_path


def test_maestro_stop(mock_dependencies, tmp_path):
    """Stop should delegate to player and reset countdown."""
    app = Maestro(songs_folder=tmp_path)
    app._countdown = 2
    app.stop()
    mock_dependencies['player'].stop.assert_called_once()
    assert app._countdown == 0


def test_maestro_play(mock_dependencies, tmp_path):
    """Play should delegate to player."""
    from maestro.player import PlaybackState
    app = Maestro(songs_folder=tmp_path)
    mock_dependencies['player'].current_song = Path("test.mid")
    mock_dependencies['player'].state = PlaybackState.STOPPED
    app.play()
    mock_dependencies['player'].play.assert_called_once()


def test_maestro_get_state_with_countdown(mock_dependencies, tmp_path):
    """State string should show countdown when counting."""
    app = Maestro(songs_folder=tmp_path)
    app._countdown = 2
    state = app._get_state_string()
    assert state == "Starting in 2..."
