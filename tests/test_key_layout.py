from maestro.key_layout import KeyLayout


def test_key_layout_has_five_members():
    """KeyLayout enum should have exactly 5 members."""
    assert len(KeyLayout) == 5


def test_iteration_order():
    """Members should iterate in definition order."""
    members = list(KeyLayout)
    assert members == [
        KeyLayout.KEYS_22,
        KeyLayout.KEYS_15_DOUBLE,
        KeyLayout.KEYS_15_TRIPLE,
        KeyLayout.DRUMS,
        KeyLayout.XYLOPHONE,
    ]
