"""
Reporting functions available to transform field data to various derived quantities.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from collections import namedtuple
from enum import Enum

import numpy as np
import unyt

from ..enums import FieldType
from .field_components import FieldComponents
from .scales import PlotScales

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


def field_quantity_e(field):
    return field["E"]


def field_quantity_gain(field):
    if (
        "gain_calibration" in field.attrs
        and field.attrs["gain_calibration"] is not None
    ):
        gain_cal_node = field.attrs["gain_calibration"]
        gain_cal_table = gain_cal_node.gain_cal_ref.data
        gain_cal_field = gain_cal_node.gain_cal_field.data

        frequency = field["frequency"].item()

        print(f"{frequency=}")

        # Configure gain cal interpolation
        gain_cal_interp = gain_cal_table.interp(
            frequency=frequency, method="linear", assume_sorted=True
        )

        # Take amplitude norm over phi/theta dimensions at current frequency
        amp_meas = np.sqrt((np.abs(field["E"]) ** 2).sum(dim="component"))

        gain_cal_field_slice = gain_cal_field["E"].sel(frequency=frequency)
        amp_ref = np.sqrt((np.abs(gain_cal_field_slice) ** 2).sum(dim="component"))

        calibrated_gain_dbi = gain_cal_interp + 20 * np.log10(amp_meas / amp_ref.max())
        calibrated_gain = 10 ** ((calibrated_gain_dbi) / 10)

        return calibrated_gain


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
        function=field_quantity_gain,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_10),
        field_types={FieldType.FAR},  # ratio
        field_components=FieldComponents,
        enabled=lambda field: (
            "gain_calibration" in field.attrs
            and field.attrs["gain_calibration"] is not None
        ),
        units="dBi",
    )
