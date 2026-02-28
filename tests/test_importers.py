"""Tests for the importers package."""

from unittest.mock import Mock, patch

import pytest

from maestro.gui.workers import DemucsDownloadWorker, ImportWorker
from maestro.importers.online_sequencer import (
    download_midi,
    extract_sequence_id,
    fetch_song_title,
)
from maestro.importers.youtube import (
    download_audio,
    extract_video_id,
    is_demucs_available,
    isolate_piano,
    transcribe_audio,
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


# ── YouTube importer tests ──────────────────────────────────────────────


class TestExtractVideoId:
    def test_standard_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        assert (
            extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42")
            == "dQw4w9WgXcQ"
        )

    def test_embed_url(self):
        assert (
            extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        )

    def test_invalid_url_returns_none(self):
        assert extract_video_id("https://onlinesequencer.net/123") is None

    def test_empty_string_returns_none(self):
        assert extract_video_id("") is None


class TestDownloadAudio:
    @patch("maestro.importers.youtube.yt_dlp.YoutubeDL")
    def test_downloads_audio_and_returns_path_and_title(self, mock_ydl_class, tmp_path):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info.return_value = {
            "title": "Piano Cover - Moonlight Sonata",
            "id": "abc123",
        }
        # Simulate the downloaded file existing
        audio_file = tmp_path / "abc123.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        path, title = download_audio("https://youtube.com/watch?v=abc123", tmp_path)
        assert title == "Piano Cover - Moonlight Sonata"
        mock_ydl.extract_info.assert_called_once()

    @patch("maestro.importers.youtube.yt_dlp.YoutubeDL")
    def test_raises_on_download_failure(self, mock_ydl_class, tmp_path):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("Download failed")

        with pytest.raises(Exception, match="Download failed"):
            download_audio("https://youtube.com/watch?v=abc123", tmp_path)


class TestTranscribeAudio:
    @patch("basic_pitch.inference.predict")
    def test_transcribes_and_saves_midi(self, mock_predict, tmp_path):
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"RIFF" + b"\x00" * 100)

        # Mock basic-pitch predict to return a mock MIDI object
        mock_midi = Mock()
        mock_predict.return_value = (mock_midi, [], [])

        result = transcribe_audio(audio_path, tmp_path, "Test Song")
        assert result.suffix == ".mid"
        assert "Test Song" in result.name
        mock_midi.write.assert_called_once()


class TestIsDemucsAvailable:
    def test_returns_false_when_model_missing(self, tmp_path):
        assert is_demucs_available(tmp_path / "nonexistent") is False

    def test_returns_true_when_model_exists(self, tmp_path):
        model_dir = tmp_path / "htdemucs"
        model_dir.mkdir()
        assert is_demucs_available(model_dir) is True


class TestIsolatePiano:
    @patch("maestro.importers.youtube.subprocess.run")
    def test_runs_demucs_command(self, mock_run, tmp_path):
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"RIFF" + b"\x00" * 100)

        output_dir = tmp_path / "separated" / "htdemucs" / "audio"
        output_dir.mkdir(parents=True)
        piano_stem = output_dir / "piano.wav"
        piano_stem.write_bytes(b"RIFF" + b"\x00" * 100)

        mock_run.return_value = Mock(returncode=0)

        isolate_piano(audio_path, tmp_path)
        mock_run.assert_called_once()


# ── Synthesia detection tests ────────────────────────────────────────────

import numpy as np

from maestro.importers.synthesia import detect_synthesia_pattern


class TestSynthesiaDetection:
    def test_detects_colored_bars_above_keyboard(self):
        """A frame with colored vertical bars in the top portion and
        a horizontal bright band at the bottom should be detected as Synthesia."""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Draw a white horizontal bar at the bottom (piano keyboard area)
        frame[620:720, :] = [255, 255, 255]
        # Draw colored vertical bars in the upper portion
        for x in range(0, 1280, 20):
            color = [(0, 255, 0), (0, 0, 255), (255, 0, 0)][x // 20 % 3]
            frame[100:620, x : x + 10] = color
        assert detect_synthesia_pattern(frame) is True

    def test_rejects_plain_video_frame(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[200:400, 300:500] = [128, 128, 128]
        assert detect_synthesia_pattern(frame) is False

    def test_rejects_all_black_frame(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        assert detect_synthesia_pattern(frame) is False

    def test_rejects_all_white_frame(self):
        frame = np.ones((720, 1280, 3), dtype=np.uint8) * 255
        assert detect_synthesia_pattern(frame) is False


# ── Import worker tests ─────────────────────────────────────────────────


class TestImportWorker:
    def test_worker_has_expected_signals(self):
        worker = ImportWorker.__new__(ImportWorker)
        assert hasattr(worker, "progress")
        assert hasattr(worker, "finished")
        assert hasattr(worker, "error")

    def test_worker_stores_url_and_dest(self, tmp_path):
        worker = ImportWorker.__new__(ImportWorker)
        worker._url = "https://onlinesequencer.net/123"
        worker._dest_folder = tmp_path
        assert worker._url == "https://onlinesequencer.net/123"
        assert worker._dest_folder == tmp_path


class TestDemucsDownloadWorker:
    def test_worker_has_expected_signals(self):
        worker = DemucsDownloadWorker.__new__(DemucsDownloadWorker)
        assert hasattr(worker, "progress")
        assert hasattr(worker, "finished")
        assert hasattr(worker, "error")
