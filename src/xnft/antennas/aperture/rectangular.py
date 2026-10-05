"""
Module providing rectangular aperture fields [§12, 1].

[1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
    N.J: Wiley-Interscience, 2005.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from dataclasses import dataclass
from warnings import warn

import numpy as np
import scipy.constants as spc
import xarray as xr
from numpy.typing import NDArray

from ...common.enums import (
    CoordinateSystemType,
    FieldType,
)
from ...common.registry import registry
from ...common.types import FieldDataset

logger = logging.getLogger(__name__)


@dataclass
class RectWaveguide:
    """Dimensions in meters, band in Hz."""

    x: float  # m
    y: float  # m
    band: tuple[float, float]  # Hz


def rect_e_near_field(
    ap_x,
    ap_y,
    x_sample_vec,
    y_sample_vec,
    z_sample_vec,
    freq_sample_vec,
    amplitude=1.0,
    excitation: str = "te10",  # [te10, uniform]
):

    e_x = e_z = np.zeros(
        (x_sample_vec.size, y_sample_vec.size, 1, freq_sample_vec.size), np.complex128
    )
    e_y = amplitude * np.ones(
        (x_sample_vec.size, y_sample_vec.size, 1, freq_sample_vec.size), np.complex128
    )

    yy, xx = np.meshgrid(y_sample_vec, x_sample_vec)

    cond = (xx <= ap_x[1]) & (xx >= ap_x[0]) & (yy <= ap_y[1]) & (yy >= ap_y[0])

    e_y *= np.where(cond, 1.0, 0.0)[:, :, None, None]

    if excitation == "uniform":
        pass  # Nothing needed for uniform
    elif excitation == "te10":
        # Taper fields based on TE-10 mode
        e_y *= np.cos(np.pi / (ap_x[1] - ap_x[0]) * xx)[:, :, None, None]
    else:
        raise NotImplementedError(f"Excitation {excitation} is not yet implemented.")

    e_field = np.stack([e_x, e_y, e_z])

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "x": x_sample_vec,
            "y": y_sample_vec,
            "z": z_sample_vec,
        },
        frequency=freq_sample_vec,
        coordinate_system=CoordinateSystemType.CARTESIAN,
        field_type=FieldType.NEAR,
        data_source=registry.data_sources.get("xnft.analytic"),
    )
    return fields


def rect_e_far_field(
    ap_x: float,  # Cross-pol
    ap_y: float,  # Co-pol
    theta_sample_vec: NDArray[np.float64],
    phi_sample_vec: NDArray[np.float64],
    wavelength_array: float | NDArray,
    flip_x: bool = False,
    flip_y: bool = False,
    rotation: float = 0.0,
    r_ff: float = 100,
    amplitude: float = 1.0,
    excitation: str = "te10",  # [te10, uniform]
    apply_prop_const: bool = True,
) -> xr.Dataset:
    """Generate ideal rectangular aperture field.

    Based on derivation in [§12, 1].  It is assumed the E-field excitation is in the y-hat direction.

    Parameters
    ----------
    ap_x : float
        X-extent of the aperture (cross-pol) in meters
    ap_y : float
        Y-extent of the aperture (co-pol) in meters
    theta_sample_vec : NDArray
        1D vector of theta sample locations of the far-field in radians
    phi_sample_vec : NDArray
        1D vector of phi sample locations of the far-field in radians
    wavelength_array : float | NDArray
        Wavelengths to sample aperture at in meters
    flip_x : bool
        Flip antenna pattern 180° about the x-axis, by default False
    flip_y : bool
        Flip antenna pattern 180° about the y-axis, by default False
    rotation : float
        Counter-clockwise antenna rotation about the z-axis (if flip_x xor flip_y is True, z-axis is down), by default 0.0
    r_ff : float, optional
        Far-field radius to compute field at in meters (important for absolute phase comparisons), by default 100 m
    amplitude : float, optional
        Maximum excitation amplitude in V, by default 1.0 V
    excitation : str, optional
        Aperture excitation mode. Must be either `uniform` or `te10`, by default `te10`
    apply_prop_const : bool, optional
        Return only the real normalized weighting values, no phase or propagation loss.

    Returns
    -------
    xr.Dataset
        Dataset containing "E" fields.

    Raises
    ------
    NotImplementedError
        Excitation mode requested is not implementated.

    References
    ----------
    [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
        N.J: Wiley-Interscience, 2005.
    """
    if flip_x:
        phi_sample_vec = -phi_sample_vec
        rotation = -rotation  # Handle z-axis flip
        phi_sample_vec = -phi_sample_vec
    if flip_y:
        phi_sample_vec = np.pi - phi_sample_vec
        rotation = -rotation  # Handle z-axis flip
        phi_sample_vec = -phi_sample_vec

    # Create sampling grid
    theta_grid, phi_grid = np.meshgrid(theta_sample_vec, phi_sample_vec, indexing="ij")
    theta_grid = theta_grid[:, :, np.newaxis]
    phi_grid = phi_grid[:, :, np.newaxis]

    e_0 = amplitude

    # Compute far-field constants
    k_0 = 2.0 * np.pi / wavelength_array

    # Compute far-field distance based on aperture at spec. frequency
    d_2 = ap_x**2 + ap_y**2  # Maximum aperture extents, squared
    r_ff_min = 2.0 * d_2 / wavelength_array  # Far-field radius (m)

    if np.array(r_ff < r_ff_min).any():
        warn(
            f"Far-zone radius is {r_ff_min} m but {r_ff} m was given--far-field approximation is not valid.",
            RuntimeWarning,
        )

    # Constants from [Table 12.1, 1]

    phi_grid_local = phi_grid - rotation

    X = k_0 * ap_x / 2 * np.sin(theta_grid) * np.cos(phi_grid_local)
    Y = k_0 * ap_y / 2 * np.sin(theta_grid) * np.sin(phi_grid_local)

    if excitation == "uniform":
        cx = np.sinc(X / np.pi)
        cy = np.sinc(Y / np.pi)
        e_theta = np.sin(phi_grid_local) * cx * cy
        e_phi = np.cos(theta_grid) * np.cos(phi_grid_local) * cx * cy
    elif excitation == "te10":
        cx = np.cos(X) / (X**2 - (np.pi / 2) ** 2)
        cy = np.sinc(Y / np.pi)
        e_theta = -np.pi / 2 * np.sin(phi_grid_local) * cx * cy
        e_phi = -np.pi / 2 * np.cos(theta_grid) * np.cos(phi_grid_local) * cx * cy
    else:
        raise NotImplementedError(
            f"Excitation mode {excitation} is not yet implemented."
        )

    e_field = np.stack([e_theta, e_phi], dtype=np.complex128)

    # Include propagation effects
    if apply_prop_const:
        greens_func_ff = np.exp(-1j * k_0 * r_ff) / (2.0 * np.pi * r_ff)
        c_ff = 1j * ap_x * ap_y * k_0 * e_0
        e_field *= c_ff * greens_func_ff

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "theta": theta_sample_vec,
            "phi": phi_sample_vec,
        },
        frequency=spc.c / wavelength_array,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=registry.data_sources.get("xnft.analytic"),
    )

    return fields
