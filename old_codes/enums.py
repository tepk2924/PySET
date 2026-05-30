from enum import IntEnum

class ColorEnum(IntEnum):
    RED = 1
    GREEN = 2
    PURPLE = 3

class ShapeEnum(IntEnum):
    OVAL = 1
    DIAMOND = 2
    WAVE = 3

class FillEnum(IntEnum):
    EMPTY = 1
    HALF = 2
    FULL = 3