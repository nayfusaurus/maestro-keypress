"""Tests for the importers package."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from maestro.importers.synthesia import detect_synthesia_pattern
from maestro.importers.youtube import (
    download_audio,
    extract_video_id,
    is_demucs_available,
    isolate_piano,
    transcribe_audio,
)

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
        assert extract_video_id("https://example.com/not-a-video") is None

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

        # Mock basic-pitch predict: returns (model_output_dict, midi_data, note_events)
        mock_midi = Mock()
        mock_midi.instruments = []
        mock_midi.get_tempo_changes.return_value = (np.array([]), np.array([120.0]))
        mock_predict.return_value = ({}, mock_midi, [])

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


