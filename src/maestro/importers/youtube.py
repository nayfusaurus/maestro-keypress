"""YouTube to MIDI conversion module.

Downloads audio from YouTube via yt-dlp, optionally isolates piano
with demucs, and transcribes to MIDI with basic-pitch.
"""

import re
import subprocess
from pathlib import Path

import yt_dlp

_YT_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
]

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*]')


def extract_video_id(url: str) -> str | None:
    """Extract a YouTube video ID from various URL formats.

    Supports standard watch URLs, short youtu.be URLs, and embed URLs.
    Returns the 11-character video ID, or None if the URL doesn't match.
    """
    for pattern in _YT_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def _sanitize_filename(name: str) -> str:
    """Replace unsafe filesystem characters with underscores."""
    return _UNSAFE_CHARS.sub("_", name).strip()


def download_audio(url: str, dest_folder: Path) -> tuple[Path, str]:
    """Download audio from a YouTube URL as WAV.

    Returns a tuple of (audio_path, title). Uses yt-dlp with FFmpeg
    post-processing to extract audio in WAV format.

    Raises on download failure.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "outtmpl": str(dest_folder / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", info.get("id", "unknown"))
        video_id = info.get("id", "unknown")

    audio_path = dest_folder / f"{video_id}.wav"
    if not audio_path.exists():
        for ext in ["m4a", "mp3", "opus", "webm"]:
            alt = dest_folder / f"{video_id}.{ext}"
            if alt.exists():
                audio_path = alt
                break

    return audio_path, title


def transcribe_audio(audio_path: Path, dest_folder: Path, title: str) -> Path:
    """Transcribe an audio file to MIDI using basic-pitch.

    Uses a lazy import to avoid loading tensorflow at module import time.
    Returns the path to the generated MIDI file.
    """
    from basic_pitch.inference import predict

    midi_data, _, _ = predict(str(audio_path))

    filename = f"{_sanitize_filename(title)}.mid"
    output_path = dest_folder / filename
    midi_data.write(str(output_path))
    return output_path


def is_demucs_available(model_dir: Path) -> bool:
    """Check if a demucs model directory exists.

    Returns True if the model directory is present, False otherwise.
    """
    return model_dir.is_dir()


def isolate_piano(audio_path: Path, output_dir: Path) -> Path:
    """Isolate piano stem from an audio file using demucs.

    Runs demucs as a subprocess with the htdemucs model and --two-stems piano.
    Returns the path to the isolated piano WAV file.

    Raises RuntimeError if demucs fails.
    """
    result = subprocess.run(
        [
            "python",
            "-m",
            "demucs",
            "--two-stems",
            "piano",
            "-o",
            str(output_dir / "separated"),
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed: {result.stderr}")

    stem_name = audio_path.stem
    piano_path = output_dir / "separated" / "htdemucs" / stem_name / "piano.wav"
    return piano_path
