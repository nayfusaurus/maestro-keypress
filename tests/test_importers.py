"""Tests for the importers package."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from maestro.importers.synthesia import detect_synthesia_pattern
from maestro.importers.youtube import (
    cleanup_temp_files,
    download_audio,
    extract_video_id,
    find_existing_import,
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
        # Two context managers: metadata phase + download phase
        mock_meta_ydl = Mock()
        mock_meta_ydl.extract_info.return_value = {
            "title": "Piano Cover - Moonlight Sonata",
            "id": "abc123",
            "duration": 300,
        }
        mock_dl_ydl = Mock()

        meta_cm = Mock()
        meta_cm.__enter__ = Mock(return_value=mock_meta_ydl)
        meta_cm.__exit__ = Mock(return_value=False)

        dl_cm = Mock()
        dl_cm.__enter__ = Mock(return_value=mock_dl_ydl)
        dl_cm.__exit__ = Mock(return_value=False)

        mock_ydl_class.side_effect = [meta_cm, dl_cm]

        # Simulate the downloaded file existing
        audio_file = tmp_path / "abc123.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        path, title, video_id = download_audio("https://youtube.com/watch?v=abc123", tmp_path)
        assert title == "Piano Cover - Moonlight Sonata"
        assert video_id == "abc123"
        mock_meta_ydl.extract_info.assert_called_once_with(
            "https://youtube.com/watch?v=abc123", download=False
        )
        mock_dl_ydl.download.assert_called_once_with(["https://youtube.com/watch?v=abc123"])

    @patch("maestro.importers.youtube.yt_dlp.YoutubeDL")
    def test_raises_on_download_failure(self, mock_ydl_class, tmp_path):
        mock_meta_ydl = Mock()
        mock_meta_ydl.extract_info.side_effect = Exception("Download failed")

        meta_cm = Mock()
        meta_cm.__enter__ = Mock(return_value=mock_meta_ydl)
        meta_cm.__exit__ = Mock(return_value=False)

        mock_ydl_class.return_value = meta_cm

        with pytest.raises(Exception, match="Download failed"):
            download_audio("https://youtube.com/watch?v=abc123", tmp_path)

    @patch("maestro.importers.youtube.yt_dlp.YoutubeDL")
    def test_rejects_video_over_max_duration(self, mock_ydl_class, tmp_path):
        mock_meta_ydl = Mock()
        mock_meta_ydl.extract_info.return_value = {
            "title": "Very Long Video",
            "id": "long123",
            "duration": 1200,
        }

        meta_cm = Mock()
        meta_cm.__enter__ = Mock(return_value=mock_meta_ydl)
        meta_cm.__exit__ = Mock(return_value=False)

        mock_ydl_class.return_value = meta_cm

        with pytest.raises(ValueError, match="exceeds maximum"):
            download_audio("https://youtube.com/watch?v=long123", tmp_path)

    @patch("maestro.importers.youtube.yt_dlp.YoutubeDL")
    def test_allows_video_under_max_duration(self, mock_ydl_class, tmp_path):
        mock_meta_ydl = Mock()
        mock_meta_ydl.extract_info.return_value = {
            "title": "Short Video",
            "id": "short123",
            "duration": 300,
        }
        mock_dl_ydl = Mock()

        meta_cm = Mock()
        meta_cm.__enter__ = Mock(return_value=mock_meta_ydl)
        meta_cm.__exit__ = Mock(return_value=False)

        dl_cm = Mock()
        dl_cm.__enter__ = Mock(return_value=mock_dl_ydl)
        dl_cm.__exit__ = Mock(return_value=False)

        mock_ydl_class.side_effect = [meta_cm, dl_cm]

        # Simulate the downloaded file existing
        audio_file = tmp_path / "short123.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        path, title, video_id = download_audio("https://youtube.com/watch?v=short123", tmp_path)
        assert path == audio_file
        assert title == "Short Video"
        assert video_id == "short123"


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


class TestFindExistingImport:
    def test_existing_midi_with_video_id_detected(self, tmp_path):
        (tmp_path / "Some Song [abc123xyz00].mid").touch()
        result = find_existing_import(tmp_path, "abc123xyz00")
        assert result is not None
        assert result.name == "Some Song [abc123xyz00].mid"

    def test_no_match_returns_none(self, tmp_path):
        (tmp_path / "Other Song [xyz000000aa].mid").touch()
        result = find_existing_import(tmp_path, "abc123xyz00")
        assert result is None

    def test_matches_midi_extension(self, tmp_path):
        (tmp_path / "Song [abc123xyz00].midi").touch()
        result = find_existing_import(tmp_path, "abc123xyz00")
        assert result is not None

    def test_empty_folder_returns_none(self, tmp_path):
        result = find_existing_import(tmp_path, "abc123xyz00")
        assert result is None


class TestCleanupTempFiles:
    def test_cleanup_removes_audio_file(self, tmp_path):
        audio = tmp_path / "abc123.wav"
        audio.write_text("fake audio")
        cleanup_temp_files(audio, tmp_path)
        assert not audio.exists()

    def test_cleanup_removes_separated_directory(self, tmp_path):
        sep_dir = tmp_path / "separated" / "htdemucs" / "abc123"
        sep_dir.mkdir(parents=True)
        (sep_dir / "piano.wav").write_text("fake")
        (sep_dir / "no_piano.wav").write_text("fake")
        audio = tmp_path / "abc123.wav"
        audio.touch()
        cleanup_temp_files(audio, tmp_path)
        assert not (tmp_path / "separated").exists()
        assert not audio.exists()

    def test_cleanup_ignores_missing_files(self, tmp_path):
        audio = tmp_path / "nonexistent.wav"
        cleanup_temp_files(audio, tmp_path)  # Should not raise


class TestTranscribeAudioVideoId:
    @patch("basic_pitch.inference.predict")
    def test_output_filename_includes_video_id(self, mock_predict, tmp_path):
        mock_midi = Mock()
        mock_midi.instruments = []
        mock_midi.get_tempo_changes.return_value = (np.array([]), np.array([120.0]))
        mock_predict.return_value = ({}, mock_midi, [])
        audio = tmp_path / "test.wav"
        audio.touch()

        result = transcribe_audio(audio, tmp_path, "My Song", video_id="abc123xyz00")
        assert result.name == "My Song [abc123xyz00].mid"

    @patch("basic_pitch.inference.predict")
    def test_output_filename_without_video_id(self, mock_predict, tmp_path):
        mock_midi = Mock()
        mock_midi.instruments = []
        mock_midi.get_tempo_changes.return_value = (np.array([]), np.array([120.0]))
        mock_predict.return_value = ({}, mock_midi, [])
        audio = tmp_path / "test.wav"
        audio.touch()

        result = transcribe_audio(audio, tmp_path, "My Song")
        assert result.name == "My Song.mid"


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


