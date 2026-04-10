"""
Plotting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
from collections import namedtuple
from enum import Enum

PlotScale = namedtuple("PlotScale", ("name", "function", "unit_modifier", "enabled"))


class PlotScales(Enum):
    LINEAR = PlotScale(
        name="Linear",
        function=lambda x: x,
        unit_modifier=lambda x: x,
        enabled=True,
    )
    DECIBELS_20 = PlotScale(
        name="dB (20·log10)",
        function=lambda x: 20 * np.log10(x),
        unit_modifier=lambda x: f"dB({x})",
        enabled=True,
    )
    DECIBELS_10 = PlotScale(
        name="dB (10·log10)",
        function=lambda x: 20 * np.log10(x),
        unit_modifier=lambda x: f"dB({x})",
        enabled=True,
    )
    DEGREES = PlotScale(
        name="Degrees",
        function=lambda x: np.rad2deg(x),
        unit_modifier=lambda x: "°",
        enabled=True,
    )
    RADIANS = PlotScale(
        name="Radians",
        function=lambda x: x,
        unit_modifier=lambda x: "rad",
        enabled=True,
    )
