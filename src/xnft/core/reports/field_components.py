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
from .functions import PlotFunctions

FieldComponent = namedtuple("FieldComponent", ("name", "function", "scales", "field_types", "plot_functions", "enabled"))


def field_component_x():
    raise NotImplementedError("field_x is not yet implemented.")


def field_component_y():
    raise NotImplementedError("field_y is not yet implemented.")


def field_component_z():
    raise NotImplementedError("field_z is not yet implemented.")


def field_component_r():
    raise NotImplementedError("field_r is not yet implemented.")


def field_component_phi():
    raise NotImplementedError("field_phi is not yet implemented.")


def field_component_theta():
    raise NotImplementedError("field_theta is not yet implemented.")


def field_component_l3_ref(field: xr.DataArray):
    """Ludwig-3 Ref Polarization"""
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi / 2
    return np.abs(np.sin(phi_grid) * e_theta + np.cos(phi_grid) * e_phi)


def field_component_l3_cross(field: xr.DataArray):
    """Ludwig-3 Cross Polarization"""
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi / 2
    return np.abs(np.cos(phi_grid) * e_theta - np.sin(phi_grid) * e_phi)


class FieldComponents(Enum):
    TOTAL = FieldComponent(
        name="Total",
        function=lambda x: x,  # Pass everything through
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    X = FieldComponent(
        name="X",
        function=field_component_x,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    Y = FieldComponent(
        name="Y",
        function=field_component_y,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    Z = FieldComponent(
        name="Z",
        function=field_component_z,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    R = FieldComponent(
        name="R",
        function=field_component_r,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    THETA = FieldComponent(
        name="Theta",  # "θ",
        function=field_component_theta,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    PHI = FieldComponent(
        name="Phi",  # "φ",
        function=field_component_phi,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    LUDWIG_3_REF = FieldComponent(
        name="L3 Ref.",
        function=field_component_l3_ref,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    LUDWIG_3_CROSS = FieldComponent(
        name="L3 Cross",
        function=field_component_l3_cross,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
