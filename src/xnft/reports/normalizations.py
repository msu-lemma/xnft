"""
Reporting normalizations available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from collections import namedtuple
from enum import Enum

import numpy as np

from ..common.enums import FieldType
from .functions import PlotFunctions

PlotNorm = namedtuple(
    "PlotNorm",
    ("name", "function", "field_types", "enabled", "unit_modifier", "functions"),
)


class PlotNorms(Enum):
    LOCAL_MAXIMA = PlotNorm(
        name="Local Maxima",
        function=lambda x: x / np.max(np.abs(x)),
        unit_modifier=lambda x: "N.U.",
        enabled=True,
        field_types={FieldType.FAR},
        functions={
            PlotFunctions.MAGNITUDE,
        },
    )
    NONE = PlotNorm(
        name="None",
        function=lambda x: x,
        unit_modifier=lambda x: x,
        enabled=True,
        field_types={FieldType.NEAR, FieldType.FAR},  # ratio
        functions={PlotFunctions.MAGNITUDE, PlotFunctions.PHASE},
    )
