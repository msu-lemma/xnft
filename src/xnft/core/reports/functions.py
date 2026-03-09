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

PlotFunction = namedtuple("PlotFunction", ("name", "function", "scales", "field_types"))


def plot_mag(field: xr.DataArray):
    if len(field.shape) > 2:
        return np.linalg.norm(field, axis=0)
    else:
        return np.abs(field)


def plot_phase(field: xr.DataArray):
    if len(field.shape) > 2:
        # Only compute the x-y and phi-theta components (not the z/rho)
        return np.angle(np.sum(field[:2], axis=0))
    else:
        return np.angle(field)


def plot_phase_l3_ref(field: xr.DataArray):
    """Ludwig-3 Ref Polarization"""
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing='ij')
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi/2
    return np.abs(np.sin(phi_grid) * e_theta + np.cos(phi_grid) * e_phi)


def plot_phase_l3_cross(field: xr.DataArray):
    """Ludwig-3 Cross Polarization"""
    phi_grid, theta_grid = np.meshgrid(field.phi, field.theta, indexing='ij')
    e_theta = field.sel(component="theta")
    e_phi = field.sel(component="phi")
    phi_grid -= np.pi/2
    return np.abs(np.cos(phi_grid) * e_theta - np.sin(phi_grid) * e_phi)


class PlotFunctions(Enum):
    MAGNITUDE = PlotFunction(
        name="Magnitude",
        function=plot_mag,
        scales=(PlotScales.DECIBELS, PlotScales.LINEAR),
        field_types={FieldType.NEAR, FieldType.FAR},
    )
    PHASE = PlotFunction(
        name="Phase",
        function=plot_phase,
        scales=(PlotScales.DEGREES, PlotScales.RADIANS),
        field_types={FieldType.NEAR, FieldType.FAR},
    )

    PHASE_L3_REF = PlotFunction(
        name="E-ref (Ludwig-3)",
        function=plot_phase_l3_ref,
        scales=(PlotScales.LINEAR,),
        field_types={FieldType.FAR},
    )

    PHASE_L3_CROSS = PlotFunction(
        name="E-cross (Ludwig-3)",
        function=plot_phase_l3_cross,
        scales=(PlotScales.LINEAR,),
        field_types={FieldType.FAR},
    )
