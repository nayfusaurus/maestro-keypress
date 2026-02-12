from maestro.key_layout import KeyLayout


def test_key_layout_has_four_members():
    """KeyLayout enum should have exactly 4 members."""
    assert len(KeyLayout) == 4


def test_keys_22_value():
    """KEYS_22 should be the full 22-key layout."""
    assert KeyLayout.KEYS_22.value == "22-key (Full)"


def test_keys_15_double_value():
    """KEYS_15_DOUBLE should be the 15-key double row layout."""
    assert KeyLayout.KEYS_15_DOUBLE.value == "15-key (Double Row)"


def test_keys_15_triple_value():
    """KEYS_15_TRIPLE should be the 15-key triple row layout."""
    assert KeyLayout.KEYS_15_TRIPLE.value == "15-key (Triple Row)"


def test_drums_value():
    """DRUMS should be the Conga/Cajon layout."""
    assert KeyLayout.DRUMS.value == "Conga/Cajon (8-key)"


def test_iteration_order():
    """Members should iterate in definition order."""
    members = list(KeyLayout)
    assert members == [
        KeyLayout.KEYS_22,
        KeyLayout.KEYS_15_DOUBLE,
        KeyLayout.KEYS_15_TRIPLE,
        KeyLayout.DRUMS,
    ]
