"""Download ffmpeg/ffprobe static binaries for bundling with PyInstaller.

Downloads the essentials build from gyan.dev (Windows) and extracts
ffmpeg.exe and ffprobe.exe into assets/ffmpeg/.

Usage:
    python scripts/download_ffmpeg.py
"""

import io
import platform
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

PROJ_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = PROJ_ROOT / "assets" / "ffmpeg"

# gyan.dev essentials build — small (~80MB zip, ~200MB extracted)
FFMPEG_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)


def download_ffmpeg_windows() -> None:
    """Download and extract ffmpeg for Windows."""
    print(f"Downloading ffmpeg from {FFMPEG_URL}...")
    req = Request(FFMPEG_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp = urlopen(req, timeout=120)  # noqa: S310

    # Read into memory with progress
    data = io.BytesIO()
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    while True:
        chunk = resp.read(8192)
        if not chunk:
            break
        data.write(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded * 100 // total
            print(f"\r  {downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB ({pct}%)", end="", flush=True)
    print()

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting ffmpeg.exe and ffprobe.exe...")
    with zipfile.ZipFile(data) as zf:
        extracted = 0
        for info in zf.infolist():
            name = Path(info.filename).name
            if name in ("ffmpeg.exe", "ffprobe.exe"):
                info.filename = name  # Flatten directory structure
                zf.extract(info, DEST_DIR)
                extracted += 1
                print(f"  Extracted: {name}")
        if extracted < 2:
            print("WARNING: Could not find both ffmpeg.exe and ffprobe.exe in archive")
            return

    print(f"Done! Binaries saved to {DEST_DIR}")


def main() -> None:
    if platform.system() != "Windows":
        print("This script downloads Windows ffmpeg binaries.")
        print("On Linux/macOS, install ffmpeg via your package manager:")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS: brew install ffmpeg")
        return

    if (DEST_DIR / "ffmpeg.exe").exists() and (DEST_DIR / "ffprobe.exe").exists():
        print(f"ffmpeg binaries already exist in {DEST_DIR}")
        print("Delete them first if you want to re-download.")
        return

    download_ffmpeg_windows()


if __name__ == "__main__":
    main()
