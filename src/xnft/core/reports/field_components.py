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

FieldComponent = namedtuple(
    "FieldComponent", ("name", "function", "scales", "field_types", "plot_functions", "enabled")
)


def field_component_x(field: xr.DataArray):
    print(field)
    if field.attrs["field_type"] == FieldType.FAR:
        phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
        e_theta = field.sel(component="theta")
        e_phi = field.sel(component="phi")
        e_r = field.sel(component="r") if "r" in field.component else 0
        phi_grid -= np.pi / 2
        return (
            np.sin(theta_grid) * np.cos(phi_grid) * e_r
            + np.cos(theta_grid) * np.cos(phi_grid) * e_theta
            - np.sin(phi_grid) * e_phi
        )
    elif field.attrs["field_type"] == FieldType.NEAR:
        return field.sel(component="x")


def field_component_y(field: xr.DataArray):
    if field.attrs["field_type"] == FieldType.FAR:
        phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
        e_theta = field.sel(component="theta")
        e_phi = field.sel(component="phi")
        e_r = field.sel(component="r") if "r" in field.component else 0
        phi_grid -= np.pi / 2
        return (
            np.sin(theta_grid) * np.sin(phi_grid) * e_r
            + np.cos(theta_grid) * np.sin(phi_grid) * e_theta
            + np.cos(phi_grid) * e_phi
        )
    elif field.attrs["field_type"] == FieldType.NEAR:
        return field.sel(component="y")


def field_component_z(field: xr.DataArray):
    if field.attrs["field_type"] == FieldType.FAR:
        phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
        e_theta = field.sel(component="theta")
        e_r = field.sel(component="r") if "r" in field.component else 0
        phi_grid -= np.pi / 2
        return np.cos(theta_grid) * e_r - np.sin(theta_grid) * e_theta
    elif field.attrs["field_type"] == FieldType.NEAR:
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
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi / 2
    return np.sin(phi_grid) * e_theta + np.cos(phi_grid) * e_phi


def field_component_l3_cross(field: xr.DataArray):
    """Ludwig-3 Cross Polarization"""
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing="ij")
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi / 2
    return np.cos(phi_grid) * e_theta - np.sin(phi_grid) * e_phi


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
        enabled=True,
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
