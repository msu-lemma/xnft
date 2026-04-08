"""
Plotting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
from collections import namedtuple
from enum import Enum

PlotScale = namedtuple("PlotScale", ("name", "function", "unit", "enabled"))


class PlotScales(Enum):
    LINEAR = PlotScale(
        name="Linear",
        function=lambda x: x,
        unit=None,
        enabled=True,
    )
    DECIBELS = PlotScale(
        name="Decibels",
        function=lambda x: 20 * np.log10(x),
        unit="dB",
        enabled=True,
    )
    DEGREES = PlotScale(
        name="Degrees",
        function=lambda x: np.rad2deg(x),
        unit="°",
        enabled=True,
    )
    RADIANS = PlotScale(
        name="Radians",
        function=lambda x: x,
        unit="rad",
        enabled=True,
    )
