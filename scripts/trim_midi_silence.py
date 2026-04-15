#!/usr/bin/env python3
"""Trim leading silence from MIDI files."""

import argparse
import sys

import mido


def trim_silence(path: str, *, dry_run: bool = False) -> None:
    mid = mido.MidiFile(path)
    original_length = mid.length
    trimmed = False

    for i, track in enumerate(mid.tracks):
        cumulative = 0
        for j, msg in enumerate(track):
            cumulative += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                break
            if msg.time > 0 and cumulative > 0:
                # Only trim if this gap leads up to the first note
                continue
        else:
            continue  # no notes in this track

        # Find total silence before first note and remove it
        silence = 0
        for k, msg in enumerate(track):
            if msg.type == "note_on" and msg.velocity > 0:
                break
            silence += msg.time

        if silence == 0:
            continue

        # Remove silence by zeroing time on messages before first note
        remaining = silence
        for k, msg in enumerate(track):
            if msg.type == "note_on" and msg.velocity > 0:
                break
            if msg.time > 0:
                remaining -= msg.time
                track[k] = msg.copy(time=0)
                trimmed = True

        ticks_per_beat = mid.ticks_per_beat
        # Find tempo for time conversion
        tempo = 500000  # default 120 BPM
        for t in mid.tracks:
            for msg in t:
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    break
            else:
                continue
            break

        seconds = mido.tick2second(silence, ticks_per_beat, tempo)
        print(f"  Track {i}: trimmed {silence} ticks ({seconds:.1f}s) of silence")

    if not trimmed:
        print(f"{path}: no leading silence found")
        return

    if dry_run:
        print(f"{path}: would trim {original_length:.1f}s → {mid.length:.1f}s")
    else:
        mid.save(path)
        print(f"{path}: {original_length:.1f}s → {mid.length:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trim leading silence from MIDI files")
    parser.add_argument("files", nargs="+", help="MIDI files to trim")
    parser.add_argument("--dry-run", action="store_true", help="show what would be trimmed without saving")
    args = parser.parse_args()

    for path in args.files:
        try:
            trim_silence(path, dry_run=args.dry_run)
        except Exception as e:
            print(f"{path}: error - {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
