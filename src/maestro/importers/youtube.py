"""YouTube to MIDI conversion module.

Downloads audio from YouTube via yt-dlp, optionally isolates piano
with demucs, and transcribes to MIDI with basic-pitch.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import yt_dlp

if TYPE_CHECKING:
    import pretty_midi


def _get_ffmpeg_location() -> str | None:
    """Return the directory containing ffmpeg/ffprobe, or None if on PATH.

    Search order:
    1. PyInstaller bundle (next to exe)
    2. System PATH (shutil.which)
    3. Common Windows install locations (winget, chocolatey, scoop, manual)

    Returns a directory path for yt-dlp's ffmpeg_location option.
    """
    # 1. PyInstaller frozen build — binaries are extracted to sys._MEIPASS
    #    (onefile) or live next to sys.executable (onedir). Check both.
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and (Path(meipass) / "ffmpeg.exe").exists():
            return str(meipass)
        exe_dir = str(Path(sys.executable).parent)
        if (Path(exe_dir) / "ffmpeg.exe").exists():
            return exe_dir
        # Fallback: return exe dir and let yt-dlp report the error
        return exe_dir

    # 2. Already on PATH — no override needed
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return None

    # 3. Search common Windows install locations
    if sys.platform == "win32":
        search_dirs = []
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            # winget installs here
            winget_base = Path(local_app) / "Microsoft" / "WinGet" / "Links"
            search_dirs.append(winget_base)
            # winget package directory (varies by version)
            winget_pkgs = Path(local_app) / "Microsoft" / "WinGet" / "Packages"
            if winget_pkgs.is_dir():
                for pkg_dir in winget_pkgs.iterdir():
                    if "ffmpeg" in pkg_dir.name.lower():
                        # Look for bin/ or the package root
                        bin_dir = pkg_dir / "ffmpeg" / "bin"
                        if bin_dir.is_dir():
                            search_dirs.append(bin_dir)
                        for sub in pkg_dir.rglob("ffmpeg.exe"):
                            search_dirs.append(sub.parent)
                            break
        # Chocolatey
        choco = Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey"))  # noqa: SIM112
        search_dirs.append(choco / "bin")
        # Scoop
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            search_dirs.append(Path(userprofile) / "scoop" / "shims")
        # Common manual install locations
        search_dirs.extend(
            [
                Path(r"C:\ffmpeg\bin"),
                Path(r"C:\Program Files\ffmpeg\bin"),
            ]
        )

        for d in search_dirs:
            if d.is_dir() and (d / "ffmpeg.exe").exists():
                return str(d)

    return None


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


def download_audio(
    url: str,
    dest_folder: Path,
    progress_callback: Callable[[float], None] | None = None,
) -> tuple[Path, str]:
    """Download audio from a YouTube URL as WAV.

    Returns a tuple of (audio_path, title). Uses yt-dlp with FFmpeg
    post-processing to extract audio in WAV format.

    If *progress_callback* is provided it will be called with a float
    in [0.0, 1.0] representing the download fraction.

    Raises on download failure.
    """
    ydl_opts: dict = {
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

    if progress_callback is not None:

        def _hook(d: dict) -> None:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    progress_callback(d.get("downloaded_bytes", 0) / total)

        ydl_opts["progress_hooks"] = [_hook]

    ffmpeg_loc = _get_ffmpeg_location()
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

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

    if not audio_path.exists():
        raise RuntimeError(f"Download produced no audio file for '{title}'")

    return audio_path, title


def _trim_leading_silence(midi_data: pretty_midi.PrettyMIDI, lead_in: float = 0.05) -> None:
    """Shift all MIDI notes so the first note starts at `lead_in` seconds.

    Modifies midi_data in place. If there are no notes, does nothing.
    """
    import logging

    logger = logging.getLogger("maestro")

    # Find the earliest note start across all instruments
    earliest = float("inf")
    for inst in midi_data.instruments:
        for note in inst.notes:
            if note.start < earliest:
                earliest = note.start

    if earliest == float("inf") or earliest <= lead_in:
        return

    shift = earliest - lead_in
    logger.info("Trimming %.2fs of leading silence", shift)

    for inst in midi_data.instruments:
        for note in inst.notes:
            note.start = max(0.0, note.start - shift)
            note.end = max(note.start + 0.01, note.end - shift)


def transcribe_audio(audio_path: Path, dest_folder: Path, title: str) -> Path:
    """Transcribe an audio file to MIDI using basic-pitch.

    Uses a lazy import to avoid loading tensorflow at module import time.
    Returns the path to the generated MIDI file.
    """
    import logging

    logger = logging.getLogger("maestro")

    from basic_pitch.inference import predict

    logger.info("Starting transcription of %s", audio_path)
    # predict() returns (model_output_dict, midi_data, note_events_list)
    #
    # Tuning for in-game piano playback:
    #   onset_threshold  0.4  – balance precision vs false onsets from sustain/harmonics
    #   frame_threshold  0.25 – balance sensitivity vs noise
    #   minimum_note_length 80 – reduce note fragmentation while keeping fast runs
    #   frequency bounds     – restrict to piano range C3-C6 (~130-1050 Hz)
    #                          filters out bass, drums, vocals as ghost notes
    _, midi_data, _ = predict(
        str(audio_path),
        onset_threshold=0.4,
        frame_threshold=0.25,
        minimum_note_length=80,
        minimum_frequency=130.0,
        maximum_frequency=1050.0,
    )
    logger.info("Transcription complete, %d instruments found", len(midi_data.instruments))

    # Trim leading silence: shift all notes so the first note starts at 50ms
    _trim_leading_silence(midi_data, lead_in=0.05)

    # Post-process: filter noise, merge fragments, simplify chords, quantize
    from maestro.importers.midi_cleanup import cleanup_transcription

    cleanup_transcription(midi_data)

    filename = f"{_sanitize_filename(title)}.mid"
    output_path = dest_folder / filename
    midi_data.write(str(output_path))
    logger.info("MIDI saved to %s", output_path)
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
    result = subprocess.run(  # nosec B603 B607
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
