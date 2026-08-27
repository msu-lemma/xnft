"""
Reporting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
import xarray as xr
from enum import Enum
from collections import namedtuple

from .scales import PlotScales
from ..enums import FieldType

PlotFunction = namedtuple(
    "PlotFunction", ("name", "name_short", "function", "scales", "field_types", "enabled")
)


def plot_mag(field: xr.DataArray, dim=2):
    """Plot magnitude of a quantity

    Parameters
    ----------
    field : xr.DataArray
        Field the function is applied to.
    dim : int, optional
        Number of dimensions remaining after transform, by default 2

    Returns
    -------
    ArrayLike
        Field value after function is applied
    """
    if len(field.shape) >= dim + 1:
        return np.linalg.norm(field, axis=0)
    else:
        return np.abs(field)


def plot_phase(field: xr.DataArray, dim=2):
    """Plot phase angle of a quantity

    Parameters
    ----------
    field : xr.DataArray
        Field the function is applied to.
    dim : int, optional
        Number of dimensions remaining after transform, by default 2

    Returns
    -------
    ArrayLike
        Field value after function is applied
    """
    if len(field.shape) >= dim + 1:
        # Only compute the x-y and phi-theta components (not the z/rho)
        return np.angle(np.sum(field[:2], axis=0))
    else:
        return np.angle(field)


class PlotFunctions(Enum):
    MAGNITUDE = PlotFunction(
        name="Magnitude",
        name_short="mag",
        function=plot_mag,
        scales=(PlotScales.DECIBELS_20, PlotScales.DECIBELS_10, PlotScales.LINEAR),
        field_types=(FieldType.NEAR, FieldType.FAR),
        enabled=True,
    )

    PHASE = PlotFunction(
        name="Phase",
        name_short="ang",
        function=plot_phase,
        scales=(PlotScales.DEGREES, PlotScales.RADIANS),
        field_types=(FieldType.NEAR, FieldType.FAR),
        enabled=True,
    )
