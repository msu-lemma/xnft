"""
Plotting functions available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
import xarray as xr
from enum import Enum
from collections import namedtuple
import unyt

from .scales import PlotScales
from ..enums import FieldType
from .field_components import FieldComponents

FieldQuantity = namedtuple(
    "FieldQuantity",
    ("name", "function", "scales", "units", "field_types", "field_components", "enabled"),
)


# -------------- Field Quantities ------------------


def field_quantity_re():
    raise NotImplementedError("field_quantity_re is not yet implemented.")


def field_quantity_gain():
    raise NotImplementedError("field_quantity_gain is not yet implemented.")


class FieldQuantities(Enum):
    RE = FieldQuantity(
        name="rE",
        function=field_quantity_re,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS),
        field_types=(FieldType.NEAR, FieldType.FAR),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=True,
        units=unyt.volt / unyt.meter,
    )
    GAIN = FieldQuantity(
        name="Gain",
        function=field_quantity_gain,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS),
        field_types=(FieldType.FAR),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=False,
        units=None,
    )
