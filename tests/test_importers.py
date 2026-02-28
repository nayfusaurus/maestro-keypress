"""Tests for the importers package."""

from unittest.mock import Mock, patch

import pytest

from maestro.importers.online_sequencer import (
    download_midi,
    extract_sequence_id,
    fetch_song_title,
)


class TestExtractSequenceId:
    def test_full_url(self):
        assert extract_sequence_id("https://onlinesequencer.net/5226854") == "5226854"

    def test_url_with_trailing_slash(self):
        assert extract_sequence_id("https://onlinesequencer.net/5226854/") == "5226854"

    def test_url_with_http(self):
        assert extract_sequence_id("http://onlinesequencer.net/1234") == "1234"

    def test_url_without_scheme(self):
        assert extract_sequence_id("onlinesequencer.net/5226854") == "5226854"

    def test_invalid_url_returns_none(self):
        assert extract_sequence_id("https://youtube.com/watch?v=abc") is None

    def test_empty_string_returns_none(self):
        assert extract_sequence_id("") is None

    def test_url_with_www(self):
        assert extract_sequence_id("https://www.onlinesequencer.net/5226854") == "5226854"


class TestFetchSongTitle:
    @patch("maestro.importers.online_sequencer.requests.get")
    def test_extracts_title_from_page(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<title>My Cool Song - Online Sequencer</title>'
        mock_get.return_value = mock_response
        assert fetch_song_title("5226854") == "My Cool Song"

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_returns_none_on_403(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        assert fetch_song_title("5226854") is None

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_returns_none_on_network_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")
        assert fetch_song_title("5226854") is None

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_returns_none_when_no_title_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No title here</body></html>'
        mock_get.return_value = mock_response
        assert fetch_song_title("5226854") is None


class TestDownloadMidi:
    @patch("maestro.importers.online_sequencer.requests.get")
    def test_downloads_and_saves_midi(self, mock_get, tmp_path):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"MThd\x00\x00\x00\x06"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        result = download_midi("5226854", tmp_path, title="My Song")
        assert result == tmp_path / "My Song.mid"
        assert result.exists()
        assert result.read_bytes() == b"MThd\x00\x00\x00\x06"

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_falls_back_to_sequence_id_filename(self, mock_get, tmp_path):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"MThd\x00\x00\x00\x06"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        result = download_midi("5226854", tmp_path, title=None)
        assert result == tmp_path / "5226854.mid"

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_raises_on_download_failure(self, mock_get, tmp_path):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response
        with pytest.raises(Exception, match="Not found"):
            download_midi("5226854", tmp_path)

    @patch("maestro.importers.online_sequencer.requests.get")
    def test_sanitizes_filename(self, mock_get, tmp_path):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"MThd\x00\x00\x00\x06"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        result = download_midi("123", tmp_path, title='Song / With : Bad * Chars')
        assert result.exists()
        assert "/" not in result.name
        assert ":" not in result.name
        assert "*" not in result.name
