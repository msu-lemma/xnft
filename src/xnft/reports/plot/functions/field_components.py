"""
Reporting functions available to retrieve field components from data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from collections import namedtuple
from enum import Enum

import numpy as np
import xarray as xr

from ....common.enums import FieldType
from .functions import PlotFunctions
from .scales import PlotScales

FieldComponent = namedtuple(
    "FieldComponent",
    ("name", "function", "scales", "field_types", "plot_functions", "enabled"),
)


def field_component_x(field: xr.DataArray):
    if field.attrs["field_type"] == FieldType.FAR:
        theta_grid = field.coords["theta"]
        phi_grid = field.coords["phi"]
        e_theta = field.sel(component="theta")
        e_phi = field.sel(component="phi")
        e_r = field.sel(component="r") if "r" in field.component else 0
        return (
            np.sin(theta_grid) * np.cos(phi_grid) * e_r
            + np.cos(theta_grid) * np.cos(phi_grid) * e_theta
            - np.sin(phi_grid) * e_phi
        )
    if field.attrs["field_type"] == FieldType.NEAR:
        return field.sel(component="x")


def field_component_y(field: xr.DataArray):
    if field.attrs["field_type"] == FieldType.FAR:
        theta_grid = field.coords["theta"]
        phi_grid = field.coords["phi"]
        e_theta = field.sel(component="theta")
        e_phi = field.sel(component="phi")
        e_r = field.sel(component="r") if "r" in field.component else 0
        return (
            np.sin(theta_grid) * np.sin(phi_grid) * e_r
            + np.cos(theta_grid) * np.sin(phi_grid) * e_theta
            + np.cos(phi_grid) * e_phi
        )
    if field.attrs["field_type"] == FieldType.NEAR:
        return field.sel(component="y")


def field_component_z(field: xr.DataArray):
    if field.attrs["field_type"] == FieldType.FAR:
        theta_grid = field.coords["theta"]
        e_theta = field.sel(component="theta")
        e_r = field.sel(component="r") if "r" in field.component else 0
        return np.cos(theta_grid) * e_r - np.sin(theta_grid) * e_theta
    if field.attrs["field_type"] == FieldType.NEAR:
        return field.sel(component="z")


def field_component_r(field: xr.DataArray):
    # FIXME: Handle Near-field
    return field.sel(component="r")


def field_component_phi(field: xr.DataArray):
    # FIXME: Handle Near-field
    return field.sel(component="phi")


def field_component_theta(field: xr.DataArray):
    # FIXME: Handle Near-field
    return field.sel(component="theta")


def field_component_l3_ref(field: xr.DataArray):
    """Ludwig-3 Ref Polarization"""
    phi_grid = field.coords["phi"]
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    return np.sin(phi_grid) * e_theta + np.cos(phi_grid) * e_phi


def field_component_l3_cross(field: xr.DataArray):
    """Ludwig-3 Cross Polarization"""
    phi_grid = field.coords["phi"]
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    return np.cos(phi_grid) * e_theta - np.sin(phi_grid) * e_phi


def field_component_rhcp(field: xr.DataArray):
    """Right-hand Circular Polarization"""
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    return 2**-0.5 * (e_theta + 1.0j * e_phi)


def field_component_lhcp(field: xr.DataArray):
    """Left-hand Circular Polarization"""
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    return 2**-0.5 * (e_theta - 1.0j * e_phi)


class FieldComponents(Enum):
    TOTAL = FieldComponent(
        name="Total",
        function=lambda x: x,  # Pass everything through
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions={PlotFunctions.MAGNITUDE},  # All plot functions valid
        enabled=True,
    )
    X = FieldComponent(
        name="X",
        function=field_component_x,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    Y = FieldComponent(
        name="Y",
        function=field_component_y,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    Z = FieldComponent(
        name="Z",
        function=field_component_z,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    R = FieldComponent(
        name="R",
        function=field_component_r,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=False,
    )
    THETA = FieldComponent(
        name="Theta",  # "θ",
        function=field_component_theta,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    PHI = FieldComponent(
        name="Phi",  # "φ",
        function=field_component_phi,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.NEAR, FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    LUDWIG_3_REF = FieldComponent(
        name="L3 Reference",
        function=field_component_l3_ref,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    LUDWIG_3_CROSS = FieldComponent(
        name="L3 Cross",
        function=field_component_l3_cross,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types={FieldType.FAR},
        plot_functions=PlotFunctions,  # All plot functions valid
        enabled=True,
    )
    RHCP = FieldComponent(
        name="RHCP",
        function=field_component_rhcp,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.FAR),
        plot_functions=PlotFunctions,
        enabled=True,
    )
    LHCP = FieldComponent(
        name="LHCP",
        function=field_component_lhcp,
        scales=(PlotScales.LINEAR, PlotScales.DECIBELS_20),
        field_types=(FieldType.FAR),
        plot_functions=PlotFunctions,
        enabled=True,
    )

    def __reduce_ex__(self, proto):
        # Pickles the Enum member by reference name
        return getattr, (self.__class__, self.name)
