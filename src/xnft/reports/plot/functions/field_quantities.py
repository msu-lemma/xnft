"""
Reporting functions available to transform field data to various derived quantities.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from collections import namedtuple
from enum import Enum

import xarray as xr

from ....common.enums import FieldType
from .field_components import FieldComponents
from .scales import PlotScales

logger = logging.getLogger(__name__)

FieldQuantity = namedtuple(
    "FieldQuantity",
    (
        "name",
        "function",
        "scales",
        "units",
        "field_types",
        "field_components",
        "enabled",
    ),
)


# -------------- Field Quantities ------------------


def field_quantity_e(field: xr.Dataset):
    return field["E"]


class FieldQuantities(Enum):
    RE = FieldQuantity(
        name="rE",
        function=field_quantity_e,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.FAR,),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=lambda field: True,
        units="",  # NOTE: We can't guarantee unit here
    )
    E = FieldQuantity(
        name="E",
        function=field_quantity_e,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.NEAR),  # ratio
        field_components=FieldComponents,  # All components valid
        enabled=lambda field: True,
        units="",  # NOTE: We can't guarantee unit here
    )
