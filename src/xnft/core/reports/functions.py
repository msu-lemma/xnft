"""
Plotting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
import xarray as xr
from enum import Enum
from collections import namedtuple

from .scales import PlotScales
from ..enums import FieldType

PlotFunction = namedtuple("PlotFunction", ("name", "function", "scales", "field_types", "enabled"))


def plot_mag(field: xr.DataArray):
    if len(field.shape) >= 2:
        return np.linalg.norm(field, axis=0)
    else:
        return np.abs(field)


def plot_phase(field: xr.DataArray):
    if len(field.shape) > 2:
        # Only compute the x-y and phi-theta components (not the z/rho)
        return np.angle(np.sum(field[:2], axis=0))
    else:
        return np.angle(field)


class PlotFunctions(Enum):
    MAGNITUDE = PlotFunction(
        name="Magnitude",
        function=plot_mag,
        scales=(PlotScales.DECIBELS, PlotScales.LINEAR),
        field_types=(FieldType.NEAR, FieldType.FAR),
        enabled=True,
    )

    PHASE = PlotFunction(
        name="Phase",
        function=plot_phase,
        scales=(PlotScales.DEGREES, PlotScales.RADIANS),
        field_types=(FieldType.NEAR, FieldType.FAR),
        enabled=True,
    )
