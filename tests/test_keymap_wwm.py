"""Tests for Where Winds Meet (WWM) keymap."""

from pynput.keyboard import Key

from maestro.keymap_wwm import midi_note_to_key_wwm


class TestNaturalNotes:
    """Test natural notes (C, D, E, F, G, A, B) in each octave."""

    # Low octave (C3-B3, MIDI 48-59) → Z, X, C, V, B, N, M
    def test_low_c(self):
        """C3 (MIDI 48) should map to Z key, no modifier."""
        assert midi_note_to_key_wwm(48) == ("z", None)

    def test_low_d(self):
        """D3 (MIDI 50) should map to X key, no modifier."""
        assert midi_note_to_key_wwm(50) == ("x", None)

    def test_low_e(self):
        """E3 (MIDI 52) should map to C key, no modifier."""
        assert midi_note_to_key_wwm(52) == ("c", None)

    def test_low_f(self):
        """F3 (MIDI 53) should map to V key, no modifier."""
        assert midi_note_to_key_wwm(53) == ("v", None)

    def test_low_g(self):
        """G3 (MIDI 55) should map to B key, no modifier."""
        assert midi_note_to_key_wwm(55) == ("b", None)

    def test_low_a(self):
        """A3 (MIDI 57) should map to N key, no modifier."""
        assert midi_note_to_key_wwm(57) == ("n", None)

    def test_low_b(self):
        """B3 (MIDI 59) should map to M key, no modifier."""
        assert midi_note_to_key_wwm(59) == ("m", None)

    # Medium octave (C4-B4, MIDI 60-71) → A, S, D, F, G, H, J
    def test_mid_c(self):
        """C4/Middle C (MIDI 60) should map to A key, no modifier."""
        assert midi_note_to_key_wwm(60) == ("a", None)

    def test_mid_d(self):
        """D4 (MIDI 62) should map to S key, no modifier."""
        assert midi_note_to_key_wwm(62) == ("s", None)

    def test_mid_e(self):
        """E4 (MIDI 64) should map to D key, no modifier."""
        assert midi_note_to_key_wwm(64) == ("d", None)

    def test_mid_f(self):
        """F4 (MIDI 65) should map to F key, no modifier."""
        assert midi_note_to_key_wwm(65) == ("f", None)

    def test_mid_g(self):
        """G4 (MIDI 67) should map to G key, no modifier."""
        assert midi_note_to_key_wwm(67) == ("g", None)

    def test_mid_a(self):
        """A4 (MIDI 69) should map to H key, no modifier."""
        assert midi_note_to_key_wwm(69) == ("h", None)

    def test_mid_b(self):
        """B4 (MIDI 71) should map to J key, no modifier."""
        assert midi_note_to_key_wwm(71) == ("j", None)

    # High octave (C5-B5, MIDI 72-83) → Q, W, E, R, T, Y, U
    def test_high_c(self):
        """C5 (MIDI 72) should map to Q key, no modifier."""
        assert midi_note_to_key_wwm(72) == ("q", None)

    def test_high_d(self):
        """D5 (MIDI 74) should map to W key, no modifier."""
        assert midi_note_to_key_wwm(74) == ("w", None)

    def test_high_e(self):
        """E5 (MIDI 76) should map to E key, no modifier."""
        assert midi_note_to_key_wwm(76) == ("e", None)

    def test_high_f(self):
        """F5 (MIDI 77) should map to R key, no modifier."""
        assert midi_note_to_key_wwm(77) == ("r", None)

    def test_high_g(self):
        """G5 (MIDI 79) should map to T key, no modifier."""
        assert midi_note_to_key_wwm(79) == ("t", None)

    def test_high_a(self):
        """A5 (MIDI 81) should map to Y key, no modifier."""
        assert midi_note_to_key_wwm(81) == ("y", None)

    def test_high_b(self):
        """B5 (MIDI 83) should map to U key, no modifier."""
        assert midi_note_to_key_wwm(83) == ("u", None)


class TestSharpNotes:
    """Test sharp notes return Shift modifier."""

    # Sharp notes in low octave (MIDI 48-59)
    def test_low_c_sharp(self):
        """C#3 (MIDI 49) should map to Z + Shift."""
        assert midi_note_to_key_wwm(49) == ("z", Key.shift)

    def test_low_d_sharp(self):
        """D#3 (MIDI 51) should map to X + Shift."""
        assert midi_note_to_key_wwm(51) == ("x", Key.shift)

    def test_low_f_sharp(self):
        """F#3 (MIDI 54) should map to V + Shift."""
        assert midi_note_to_key_wwm(54) == ("v", Key.shift)

    def test_low_g_sharp(self):
        """G#3 (MIDI 56) should map to B + Shift."""
        assert midi_note_to_key_wwm(56) == ("b", Key.shift)

    def test_low_a_sharp(self):
        """A#3 (MIDI 58) should map to N + Shift."""
        assert midi_note_to_key_wwm(58) == ("n", Key.shift)

    # Sharp notes in medium octave (MIDI 60-71)
    def test_mid_c_sharp(self):
        """C#4 (MIDI 61) should map to A + Shift."""
        assert midi_note_to_key_wwm(61) == ("a", Key.shift)

    def test_mid_d_sharp(self):
        """D#4 (MIDI 63) should map to S + Shift."""
        assert midi_note_to_key_wwm(63) == ("s", Key.shift)

    def test_mid_f_sharp(self):
        """F#4 (MIDI 66) should map to F + Shift."""
        assert midi_note_to_key_wwm(66) == ("f", Key.shift)

    def test_mid_g_sharp(self):
        """G#4 (MIDI 68) should map to G + Shift."""
        assert midi_note_to_key_wwm(68) == ("g", Key.shift)

    def test_mid_a_sharp(self):
        """A#4 (MIDI 70) should map to H + Shift."""
        assert midi_note_to_key_wwm(70) == ("h", Key.shift)

    # Sharp notes in high octave (MIDI 72-83)
    def test_high_c_sharp(self):
        """C#5 (MIDI 73) should map to Q + Shift."""
        assert midi_note_to_key_wwm(73) == ("q", Key.shift)

    def test_high_d_sharp(self):
        """D#5 (MIDI 75) should map to W + Shift."""
        assert midi_note_to_key_wwm(75) == ("w", Key.shift)

    def test_high_f_sharp(self):
        """F#5 (MIDI 78) should map to R + Shift."""
        assert midi_note_to_key_wwm(78) == ("r", Key.shift)

    def test_high_g_sharp(self):
        """G#5 (MIDI 80) should map to T + Shift."""
        assert midi_note_to_key_wwm(80) == ("t", Key.shift)

    def test_high_a_sharp(self):
        """A#5 (MIDI 82) should map to Y + Shift."""
        assert midi_note_to_key_wwm(82) == ("y", Key.shift)


class TestTransposition:
    """Test notes outside range (MIDI 48-83) are transposed into range."""

    def test_transpose_too_low_one_octave(self):
        """C2 (MIDI 36) should transpose up to C3 (Z key)."""
        assert midi_note_to_key_wwm(36) == ("z", None)

    def test_transpose_too_low_two_octaves(self):
        """C1 (MIDI 24) should transpose up to C3 (Z key)."""
        assert midi_note_to_key_wwm(24) == ("z", None)

    def test_transpose_too_high_one_octave(self):
        """C6 (MIDI 84) should transpose down to C5 (Q key)."""
        assert midi_note_to_key_wwm(84) == ("q", None)

    def test_transpose_too_high_two_octaves(self):
        """C7 (MIDI 96) should transpose down to C5 (Q key)."""
        assert midi_note_to_key_wwm(96) == ("q", None)

    def test_transpose_sharp_note_too_low(self):
        """C#2 (MIDI 37) should transpose to C#3 (Z + Shift)."""
        assert midi_note_to_key_wwm(37) == ("z", Key.shift)

    def test_transpose_sharp_note_too_high(self):
        """C#6 (MIDI 85) should transpose to C#5 (Q + Shift)."""
        assert midi_note_to_key_wwm(85) == ("q", Key.shift)

    def test_transpose_very_low_note(self):
        """MIDI 0 (way below range) should transpose into range."""
        key, modifier = midi_note_to_key_wwm(0)
        # MIDI 0 is C, should end up as C in one of our octaves
        assert key in ("z", "a", "q")
        assert modifier is None

    def test_transpose_very_high_note(self):
        """MIDI 127 (way above range) should transpose into range."""
        key, modifier = midi_note_to_key_wwm(127)
        # MIDI 127 is G, should end up as G in one of our octaves
        assert key in ("b", "g", "t")
        assert modifier is None


class TestExampleCases:
    """Test the example cases from the task description."""

    def test_example_middle_c(self):
        """midi_note_to_key_wwm(60) → ("a", None)  # Middle C = A key, no modifier"""
        assert midi_note_to_key_wwm(60) == ("a", None)

    def test_example_c_sharp(self):
        """midi_note_to_key_wwm(61) → ("a", Key.shift)  # C# = Shift+A"""
        assert midi_note_to_key_wwm(61) == ("a", Key.shift)

    def test_example_c5(self):
        """midi_note_to_key_wwm(72) → ("q", None)  # C5 = Q key"""
        assert midi_note_to_key_wwm(72) == ("q", None)

    def test_example_c_sharp_5(self):
        """midi_note_to_key_wwm(73) → ("q", Key.shift)  # C#5 = Shift+Q"""
        assert midi_note_to_key_wwm(73) == ("q", Key.shift)
