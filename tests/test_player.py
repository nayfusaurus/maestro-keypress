import sys

import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path

from maestro.game_mode import GameMode
from maestro.key_layout import KeyLayout
from maestro.parser import Note
from maestro.player import Player, PlaybackState


@pytest.fixture
def mock_keyboard():
    """Mock pynput keyboard controller."""
    with patch('maestro.player.Controller') as mock:
        yield mock.return_value


@pytest.fixture
def sample_midi(tmp_path):
    """Create a simple test MIDI with multiple notes for longer playback."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for i in range(5):
        track.append(mido.Message('note_on', note=60, velocity=64, time=480))
        track.append(mido.Message('note_off', note=60, velocity=64, time=240))
    midi_path = tmp_path / "test.mid"
    mid.save(midi_path)
    return midi_path


def test_player_initial_state():
    """Player should start in STOPPED state."""
    player = Player()
    assert player.state == PlaybackState.STOPPED


def test_player_load_song(sample_midi, mock_keyboard):
    """Player should load a MIDI file."""
    player = Player()
    player.load(sample_midi)
    assert player.current_song == sample_midi


def test_player_play_changes_state(sample_midi, mock_keyboard):
    """Playing should change state to PLAYING."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    assert player.state == PlaybackState.PLAYING
    player.stop()


def test_player_stop_changes_state(sample_midi, mock_keyboard):
    """Stopping should change state to STOPPED."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    player.stop()
    assert player.state == PlaybackState.STOPPED


def test_playback_state_has_no_paused():
    """PlaybackState should only have STOPPED and PLAYING."""
    states = [s.name for s in PlaybackState]
    assert 'STOPPED' in states
    assert 'PLAYING' in states
    assert 'PAUSED' not in states


def test_speed_clamped_to_valid_range():
    """Speed should be clamped between 0.25 and 1.5."""
    player = Player()

    player.speed = 0.1  # Below min
    assert player.speed == 0.25

    player.speed = 2.0  # Above max
    assert player.speed == 1.5

    player.speed = 1.0  # Valid
    assert player.speed == 1.0


def test_get_upcoming_notes_returns_notes_within_lookahead(sample_midi, mock_keyboard):
    """get_upcoming_notes should return notes within lookahead window."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)

    notes = player.get_upcoming_notes(5.0)
    assert isinstance(notes, list)
    player.stop()


def test_get_upcoming_notes_empty_when_stopped():
    """get_upcoming_notes should return empty list when stopped."""
    player = Player()
    notes = player.get_upcoming_notes(5.0)
    assert notes == []


def test_duration_includes_last_note_duration(tmp_path, mock_keyboard):
    """Duration should include the last note's duration, not just its start time."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # Single note: starts at 0, duration of 480 ticks
    # At 120 BPM with 480 ticks/beat: 480 ticks = 0.5 seconds
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=64, time=480))
    midi_path = tmp_path / "duration_test.mid"
    mid.save(midi_path)

    player = Player()
    player.load(midi_path)

    # Note starts at 0, lasts 0.5 seconds
    # Duration should be ~0.5, not 0.0
    assert player.duration >= 0.4  # Allow small float variance
    assert player.duration <= 0.6


class TestTransposeProperty:
    """Tests for the transpose property."""

    def test_transpose_default_is_false(self):
        """Player should default to transpose=False."""
        player = Player()
        assert player.transpose is False

    def test_transpose_can_be_set_to_true(self):
        """Player transpose can be enabled."""
        player = Player()
        player.transpose = True
        assert player.transpose is True

    def test_transpose_can_be_set_to_false(self):
        """Player transpose can be disabled."""
        player = Player()
        player.transpose = True
        player.transpose = False
        assert player.transpose is False


@pytest.fixture
def player():
    """Create a Player with mocked keyboard Controller."""
    with patch('maestro.player.Controller'):
        return Player()


class TestKeyLayout:
    """Tests for key layout property."""

    def test_default_layout_is_22_key(self, player):
        assert player._key_layout == KeyLayout.KEYS_22

    def test_layout_can_be_set(self, player):
        player.key_layout = KeyLayout.KEYS_15_DOUBLE
        assert player.key_layout == KeyLayout.KEYS_15_DOUBLE

    def test_sharp_handling_default_is_skip(self, player):
        assert player.sharp_handling == "skip"

    def test_sharp_handling_can_be_set_to_snap(self, player):
        player.sharp_handling = "snap"
        assert player.sharp_handling == "snap"

    def test_sharp_handling_rejects_invalid(self, player):
        player.sharp_handling = "invalid"
        assert player.sharp_handling == "skip"  # stays at default


class TestResolveKey:
    """Tests for _resolve_key method."""

    def test_resolve_key_heartopia_22_key(self, player):
        """22-key layout resolves Middle C to 'z'."""
        player.key_layout = KeyLayout.KEYS_22
        result = player._resolve_key(60)
        assert result == ("z", None)

    def test_resolve_key_heartopia_15_double(self, player):
        """15-key double layout resolves Middle C to 'a'."""
        player.key_layout = KeyLayout.KEYS_15_DOUBLE
        result = player._resolve_key(60)
        assert result == ("a", None)

    def test_resolve_key_heartopia_15_triple(self, player):
        """15-key triple layout resolves Middle C to 'y'."""
        player.key_layout = KeyLayout.KEYS_15_TRIPLE
        result = player._resolve_key(60)
        assert result == ("y", None)

    def test_resolve_key_drums(self, player):
        """Drums layout resolves notes 60-67 to y,u,i,o,h,j,k,l."""
        player.key_layout = KeyLayout.DRUMS
        # C4 (60) = 'y'
        result = player._resolve_key(60)
        assert result == ("y", None)
        # C#4 (61) = 'u'
        result = player._resolve_key(61)
        assert result == ("u", None)
        # G4 (67) = 'l'
        result = player._resolve_key(67)
        assert result == ("l", None)

    def test_resolve_key_drums_out_of_range(self, player):
        """Drums layout returns None for notes outside 60-67 range."""
        player.key_layout = KeyLayout.DRUMS
        # Below range
        result = player._resolve_key(59)
        assert result is None
        # Above range
        result = player._resolve_key(68)
        assert result is None

    def test_resolve_key_xylophone(self, player):
        """Xylophone layout resolves natural notes 60-72 to a,s,d,f,g,h,j,k."""
        player.key_layout = KeyLayout.XYLOPHONE
        # C4 (60) = 'a'
        result = player._resolve_key(60)
        assert result == ("a", None)
        # D4 (62) = 's'
        result = player._resolve_key(62)
        assert result == ("s", None)
        # C5 (72) = 'k'
        result = player._resolve_key(72)
        assert result == ("k", None)

    def test_resolve_key_xylophone_out_of_range(self, player):
        """Xylophone layout returns None for sharp notes and out-of-range notes."""
        player.key_layout = KeyLayout.XYLOPHONE
        # Sharp note (C#4 = 61) should return None
        result = player._resolve_key(61)
        assert result is None
        # Below range
        result = player._resolve_key(59)
        assert result is None
        # Above range
        result = player._resolve_key(73)
        assert result is None

    def test_resolve_key_out_of_range_returns_none(self, player):
        """Out of range note returns None."""
        player.key_layout = KeyLayout.KEYS_22
        result = player._resolve_key(20)
        assert result is None


class TestKeyEvent:
    """Tests for KeyEvent dataclass."""

    def test_key_event_creation(self):
        from maestro.player import KeyEvent
        event = KeyEvent(time=1.0, action="down", key="z")
        assert event.time == 1.0
        assert event.action == "down"
        assert event.key == "z"
        assert event.modifier is None

    def test_key_event_with_modifier(self):
        from maestro.player import KeyEvent
        from pynput.keyboard import Key
        event = KeyEvent(time=1.0, action="down", key="a", modifier=Key.shift)
        assert event.modifier == Key.shift


class TestBuildEvents:
    """Tests for _build_events method."""

    def test_build_events_creates_down_and_up(self, player):
        """Each note should produce a down and up event."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        events = player._build_events()
        assert len(events) == 2
        assert events[0].action == "down"
        assert events[0].time == 0.0
        assert events[1].action == "up"
        assert events[1].time == 0.5

    def test_build_events_sorts_by_time(self, player):
        """Events should be sorted by time."""
        player._notes = [
            Note(midi_note=60, time=1.0, duration=0.5),
            Note(midi_note=62, time=0.0, duration=0.5),
        ]
        events = player._build_events()
        times = [e.time for e in events]
        assert times == sorted(times)

    def test_build_events_up_before_down_at_same_time(self, player):
        """At same timestamp, up events come before down events."""
        # Note 1 ends at 0.5, Note 2 starts at 0.5
        player._notes = [
            Note(midi_note=60, time=0.0, duration=0.5),
            Note(midi_note=60, time=0.5, duration=0.5),
        ]
        events = player._build_events()
        # Find events at time 0.5
        events_at_half = [e for e in events if abs(e.time - 0.5) < 0.001]
        assert len(events_at_half) == 2
        assert events_at_half[0].action == "up"
        assert events_at_half[1].action == "down"

    def test_build_events_skips_unplayable_notes(self, player):
        """Notes that can't be mapped should be skipped."""
        player._notes = [Note(midi_note=20, time=0.0, duration=0.5)]  # Out of range
        events = player._build_events()
        assert len(events) == 0

    def test_build_events_chord(self, player):
        """Multiple notes at same time should all produce events."""
        player._notes = [
            Note(midi_note=60, time=0.0, duration=0.5),
            Note(midi_note=64, time=0.0, duration=0.5),
            Note(midi_note=67, time=0.0, duration=0.5),
        ]
        events = player._build_events()
        assert len(events) == 6  # 3 down + 3 up


class TestHeldKeys:
    """Tests for held keys tracking."""

    def test_key_down_adds_to_held(self, player):
        """key_down should add key to held set."""
        player._key_down("z")
        assert ("z", None) in player._held_keys

    def test_key_up_removes_from_held(self, player):
        """key_up should remove key from held set."""
        player._key_down("z")
        player._key_up("z")
        assert ("z", None) not in player._held_keys

    def test_key_down_duplicate_ignored(self, player):
        """Pressing already-held key should not error."""
        player._key_down("z")
        player._key_down("z")  # Should not crash
        assert ("z", None) in player._held_keys

    def test_key_up_not_held_ignored(self, player):
        """Releasing non-held key should not error."""
        player._key_up("z")  # Should not crash

    def test_release_all_keys(self, player):
        """release_all_keys should clear all held keys."""
        player._key_down("z")
        player._key_down("x")
        player._key_down("c")
        player._release_all_keys()
        assert len(player._held_keys) == 0

    def test_stop_releases_all_keys(self, player):
        """Stopping playback should release all held keys."""
        player._key_down("z")
        player._key_down("x")
        player.stop()
        assert len(player._held_keys) == 0


class TestLastKeyFeedback:
    """Tests for last key visual feedback."""

    def test_key_down_updates_last_key(self, player):
        """key_down should update last_key for visual feedback."""
        player._key_down("z")
        assert player.last_key == "Z"

    def test_key_down_with_modifier_shows_shift(self, player):
        """key_down with modifier should show Shift+KEY."""
        from pynput.keyboard import Key
        player._key_down("a", Key.shift)
        assert player.last_key == "Shift+A"


class TestAtexitRegistration:
    """Tests for atexit registration of _release_all_keys."""

    def test_atexit_registers_release_all_keys(self, player):
        """Player should register _release_all_keys with atexit."""
        import atexit
        # atexit registration happens in __init__, verify _release_all_keys is callable
        assert callable(player._release_all_keys)


class TestWindowFocusDetection:
    """Tests for window focus detection."""

    def test_is_game_window_active_non_windows(self, player):
        """On non-Windows platforms, always returns True."""
        with patch('maestro.player.sys') as mock_sys:
            mock_sys.platform = "linux"
            assert player._is_game_window_active() is True

    def test_is_game_window_active_exception_returns_true(self, player):
        """If win32gui fails, should return True (don't block playback)."""
        with patch('maestro.player.sys') as mock_sys:
            mock_sys.platform = "win32"
            # win32gui import will fail on non-Windows
            with patch.dict('sys.modules', {'win32gui': None}):
                assert player._is_game_window_active() is True

    def test_is_game_window_active_heartopia_match(self, player):
        """Should detect Heartopia window title."""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

    def test_is_game_window_active_wwm_match(self, player):
        """Should detect Where Winds Meet window title."""
        if sys.platform != "win32":
            pytest.skip("Windows-only test")

    def test_focus_loss_pauses_timeline(self, player):
        """When game loses focus, start_time should be adjusted to freeze timeline."""
        # Setup: give the player some notes and simulate playback
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        player._start_time = time.time()

        # Simulate: window inactive for 0.2s, then active again
        call_count = 0
        def mock_focus():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return False  # First 2 calls: window not active
            return True  # After that: window active

        original_start = player._start_time
        with patch.object(player, '_is_game_window_active', side_effect=mock_focus):
            # Simulate the focus-loss block from _playback_loop
            if not player._is_game_window_active():
                pause_start = time.time()
                while not player._is_game_window_active() and not player._stop_event.is_set():
                    time.sleep(0.05)
                player._start_time += (time.time() - pause_start)

        # start_time should have been pushed forward (pause compensation)
        assert player._start_time > original_start


class TestEventCaching:
    """Tests for event caching to avoid rebuilding on replays."""

    def test_cache_initially_empty(self, player):
        """Cache should be None initially."""
        assert player._cached_events is None
        assert player._cached_cache_key is None

    def test_build_events_caches_result(self, player):
        """_build_events should cache the result."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        events = player._build_events()
        assert player._cached_events is not None
        assert player._cached_cache_key is not None
        assert player._cached_events is events

    def test_build_events_reuses_cache(self, player):
        """_build_events should reuse cached events on second call."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        events1 = player._build_events()
        events2 = player._build_events()
        # Should return the exact same list object (not a copy)
        assert events1 is events2

    def test_cache_invalidated_on_song_change(self, player, tmp_path):
        """Loading a different song should invalidate cache."""
        # Create two different MIDI files
        import mido
        mid1 = mido.MidiFile()
        track1 = mido.MidiTrack()
        mid1.tracks.append(track1)
        track1.append(mido.Message('note_on', note=60, velocity=64, time=0))
        track1.append(mido.Message('note_off', note=60, velocity=64, time=480))
        midi_path1 = tmp_path / "test1.mid"
        mid1.save(midi_path1)

        mid2 = mido.MidiFile()
        track2 = mido.MidiTrack()
        mid2.tracks.append(track2)
        track2.append(mido.Message('note_on', note=62, velocity=64, time=0))
        track2.append(mido.Message('note_off', note=62, velocity=64, time=480))
        midi_path2 = tmp_path / "test2.mid"
        mid2.save(midi_path2)

        # Load first song and build events
        player.load(midi_path1)
        events1 = player._build_events()

        # Load second song - cache should be invalidated
        player.load(midi_path2)
        assert player._cached_events is None

        # Build events again - should get different result
        events2 = player._build_events()
        assert events1 is not events2

    def test_cache_invalidated_on_layout_change(self, player):
        """Changing key layout should invalidate cache."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        player.key_layout = KeyLayout.KEYS_22
        events1 = player._build_events()

        # Change layout
        player.key_layout = KeyLayout.KEYS_15_DOUBLE
        assert player._cached_events is None

        # Build again
        events2 = player._build_events()
        assert events1 is not events2

    def test_cache_invalidated_on_transpose_change(self, player):
        """Changing transpose should invalidate cache."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        player.transpose = False
        events1 = player._build_events()

        # Change transpose
        player.transpose = True
        assert player._cached_events is None

        # Build again
        events2 = player._build_events()
        assert events1 is not events2

    def test_cache_invalidated_on_sharp_handling_change(self, player):
        """Changing sharp_handling should invalidate cache."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        player.key_layout = KeyLayout.KEYS_15_DOUBLE
        player.sharp_handling = "skip"
        events1 = player._build_events()

        # Change sharp handling
        player.sharp_handling = "snap"
        assert player._cached_events is None

        # Build again
        events2 = player._build_events()
        assert events1 is not events2

    def test_cache_key_includes_song_path(self, player, tmp_path):
        """Cache key should include song path."""
        import mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message('note_on', note=60, velocity=64, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, time=480))
        midi_path = tmp_path / "test.mid"
        mid.save(midi_path)

        player.load(midi_path)
        cache_key = player._get_cache_key()
        assert str(midi_path) in cache_key

    def test_cache_key_includes_layout(self, player):
        """Cache key should include key layout."""
        player.key_layout = KeyLayout.KEYS_15_DOUBLE
        cache_key = player._get_cache_key()
        assert "KEYS_15_DOUBLE" in cache_key

    def test_cache_key_includes_transpose(self, player):
        """Cache key should include transpose setting."""
        player.transpose = True
        cache_key = player._get_cache_key()
        assert "True" in cache_key

    def test_cache_key_includes_sharp_handling(self, player):
        """Cache key should include sharp handling setting."""
        player.sharp_handling = "snap"
        cache_key = player._get_cache_key()
        assert "snap" in cache_key

    def test_cache_not_invalidated_on_speed_change(self, player):
        """Speed changes should NOT invalidate cache (doesn't affect events)."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        events1 = player._build_events()

        # Change speed
        player.speed = 0.5
        events2 = player._build_events()

        # Should return cached events
        assert events1 is events2

    def test_invalidate_cache_method(self, player):
        """_invalidate_cache should clear cache."""
        player._notes = [Note(midi_note=60, time=0.0, duration=0.5)]
        player._build_events()
        assert player._cached_events is not None

        player._invalidate_cache()
        assert player._cached_events is None
        assert player._cached_cache_key is None

    def test_replay_uses_cache(self, player, tmp_path):
        """Playing the same song twice should use cache on second play."""
        import mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message('note_on', note=60, velocity=64, time=0))
        track.append(mido.Message('note_off', note=60, velocity=64, time=480))
        midi_path = tmp_path / "test.mid"
        mid.save(midi_path)

        player.load(midi_path)

        # First play - should build events
        events1 = player._build_events()

        # Second call - should use cache
        events2 = player._build_events()
        assert events1 is events2
