# SPDX-License-Identifier: MPL-2.0
import mido

from maestro.gui.workers import ValidationWorker
from maestro.key_layout import KeyLayout


def test_switch_game_with_drums_selected(tmp_path):
    song = tmp_path / "high.mid"
    midi = mido.MidiFile()
    midi.add_track().extend([
        mido.Message("note_on", note=72),
        mido.Message("note_off", note=72, time=480),
    ])
    midi.save(song)
    cache, metadata, parsed = {}, {}, {}
    results = []

    def capture(path, status, info, notes, playable, total):
        metadata[path], parsed[path] = info, notes
        results.append((status, playable))

    for game in ("Heartopia", "Where Winds Meet", "Heartopia"):
        worker = ValidationWorker([song], KeyLayout.DRUMS, game, False, "skip", cache, metadata, parsed)
        worker.song_validated.connect(capture)
        worker.run()
    assert results == [("invalid", 0), ("valid", 1), ("invalid", 0)]
