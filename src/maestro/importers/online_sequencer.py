"""OnlineSequencer MIDI download module.

Downloads MIDI files from OnlineSequencer.net given a sequence URL.
Attempts to extract the song title from the page for the filename,
falls back to the sequence ID if title extraction fails.
"""

import re
from pathlib import Path

import requests

_URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?onlinesequencer\.net/(\d+)")
_MIDI_ENDPOINT = "https://onlinesequencer.net/app/midi.php?id={sequence_id}"
_PAGE_URL = "https://onlinesequencer.net/{sequence_id}"
_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*]')


def extract_sequence_id(url: str) -> str | None:
    """Extract the numeric sequence ID from an OnlineSequencer URL.

    Accepts URLs with or without scheme, with or without www prefix,
    and with or without a trailing slash.

    Returns the sequence ID string, or None if the URL doesn't match.
    """
    match = _URL_PATTERN.search(url)
    return match.group(1) if match else None


def fetch_song_title(sequence_id: str) -> str | None:
    """Fetch the song title from the OnlineSequencer page.

    Scrapes the HTML <title> tag and strips the " - Online Sequencer" suffix.
    Returns None on any failure (403, network error, missing title).
    """
    try:
        resp = requests.get(
            _PAGE_URL.format(sequence_id=sequence_id),
            timeout=10,
            headers={"User-Agent": "Maestro MIDI Player"},
        )
        if resp.status_code != 200:
            return None
        title_match = re.search(
            r"<title>(.+?)\s*-\s*Online Sequencer</title>", resp.text
        )
        if title_match:
            return title_match.group(1).strip()
        return None
    except requests.RequestException:
        return None


def _sanitize_filename(name: str) -> str:
    """Replace unsafe filesystem characters with underscores."""
    return _UNSAFE_CHARS.sub("_", name).strip()


def download_midi(
    sequence_id: str,
    dest_folder: Path,
    title: str | None = None,
) -> Path:
    """Download a MIDI file from OnlineSequencer and save it to dest_folder.

    Uses the song title for the filename if provided, otherwise falls back
    to the sequence ID. Unsafe characters are replaced with underscores.

    Raises on HTTP errors (via raise_for_status).
    """
    resp = requests.get(
        _MIDI_ENDPOINT.format(sequence_id=sequence_id),
        timeout=30,
    )
    resp.raise_for_status()

    filename = f"{_sanitize_filename(title)}.mid" if title else f"{sequence_id}.mid"

    dest = dest_folder / filename
    dest.write_bytes(resp.content)
    return dest
