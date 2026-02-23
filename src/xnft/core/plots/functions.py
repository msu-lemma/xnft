"""
Plotting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
from enum import Enum
from collections import namedtuple

from .scales import PlotScales

PlotFunction = namedtuple("PlotFunction", ("name", "function", "scales"))


class PlotFunctions(Enum):
    MAGNITUDE = PlotFunction(
        name="Magnitude",
        function=lambda x: np.linalg.norm(x, axis=0) if len(x.shape) > 2 else np.abs(x),
        scales=(PlotScales.DECIBELS, PlotScales.LINEAR),
    )
    PHASE = PlotFunction(
        name="Phase",
        function=lambda x: np.angle(np.sum(x, axis=0)) if len(x.shape) > 2 else np.angle(x),
        scales=(PlotScales.DEGREES, PlotScales.RADIANS),
    )


# TODO: Add ludwig polarization functions here
def ludwig():
    pass
