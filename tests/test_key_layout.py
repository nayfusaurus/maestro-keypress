from maestro.key_layout import KeyLayout, WwmLayout


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


def test_wwm_layout_has_two_members():
    """WwmLayout enum should have exactly 2 members."""
    assert len(WwmLayout) == 2


def test_wwm_layout_iteration_order():
    """WwmLayout members should iterate in definition order."""
    members = list(WwmLayout)
    assert members == [WwmLayout.KEYS_36, WwmLayout.KEYS_21]
