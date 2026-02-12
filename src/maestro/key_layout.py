"""Key layout selection for Heartopia instruments."""

from enum import Enum


class KeyLayout(Enum):
    KEYS_22 = "22-key (Full)"
    KEYS_15_DOUBLE = "15-key (Double Row)"
    KEYS_15_TRIPLE = "15-key (Triple Row)"
    DRUMS = "Conga/Cajon (8-key)"
    XYLOPHONE = "Xylophone (8-key)"
