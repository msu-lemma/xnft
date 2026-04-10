"""
Plotting normalizations available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
from collections import namedtuple
from enum import Enum

PlotNorm = namedtuple("PlotNorm", ("name", "function", "enabled", "unit_modifier"))


def local_maxima(x):
    raise NotImplementedError("local_maxima norm is not yet implemented")


class PlotNorms(Enum):
    LOCAL_MAXIMA = PlotNorm(name="Local Maxima", function=lambda x: x / np.max(np.abs(x)), unit_modifier=lambda x: "N.U.", enabled=True)
