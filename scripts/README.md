# Scripts

Utility scripts for Maestro.

## trim_midi_silence.py

Trims leading silence from MIDI files by removing dead time before the first note in each track.

### Usage

```bash
# Trim a single file
uv run python scripts/trim_midi_silence.py songs/my_song.mid

# Trim multiple files
uv run python scripts/trim_midi_silence.py songs/song1.mid songs/song2.mid

# Trim all MIDI files in a folder
uv run python scripts/trim_midi_silence.py songs/*.mid

# Preview changes without saving
uv run python scripts/trim_midi_silence.py --dry-run songs/my_song.mid
```

### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be trimmed without modifying files |

### Example output

```
  Track 1: trimmed 16516 ticks (8.6s) of silence
songs/my_song.mid: 248.9s → 240.4s
```

## download_ffmpeg.py

Downloads the FFmpeg binary required by yt-dlp for YouTube audio extraction.
