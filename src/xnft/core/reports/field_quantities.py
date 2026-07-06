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


def field_quantity_e(field):
    return field["E"]


def gain_norm(field):
    if "gain_calibration" in field.attrs and field.attrs["gain_calibration"] is not None:
        cal = field.attrs["gain_calibration"].gain_cal_ref
        print(f'Gain Calibration: {cal}')
        return field["E"]


class FieldQuantities(Enum):
    RE = FieldQuantity(
        name="rE",
        function=field_quantity_e,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.FAR,),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=lambda field: True,
        units=unyt.volt / unyt.meter,
    )
    E = FieldQuantity(
        name="E",
        function=field_quantity_e,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.NEAR),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=lambda field: True,
        units=unyt.volt / unyt.meter,
    )
    GAIN = FieldQuantity(
        name="Gain",
        function=gain_norm,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.FAR},  # ratio
        field_components=FieldComponents,
        enabled=lambda field: "gain_calibration" in field.attrs and field.attrs["gain_calibration"] is not None,
        units='dBi'
    )
