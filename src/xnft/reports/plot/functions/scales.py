"""
Reporting scales available.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from collections import namedtuple
from enum import Enum

import numpy as np

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
        function=lambda x: 20 * np.log10(np.clip(x, 1e-15, None)),
        unit_modifier=lambda x: f"dB({x})",
        enabled=True,
    )
    DECIBELS_10 = PlotScale(
        name="dB (10·log10)",
        function=lambda x: 10 * np.log10(np.clip(x, 1e-15, None)),
        unit_modifier=lambda x: f"dB({x})",
        enabled=True,
    )
    DEGREES = PlotScale(
        name="Degrees",
        function=np.rad2deg,
        unit_modifier=lambda x: "°",
        enabled=True,
    )
    RADIANS = PlotScale(
        name="Radians",
        function=lambda x: x,
        unit_modifier=lambda x: "rad",
        enabled=True,
    )

    def __reduce_ex__(self, proto):
        # Pickles the Enum member by reference name, e.g., getattr(PlotScales, 'LINEAR')
        return getattr, (self.__class__, self.name)
