"""
Module providing rectangular aperture fields [§12, 1].

[1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
    N.J: Wiley-Interscience, 2005.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

import scipy.constants as spc

from ...core.enums import (
    DataSourceType,
    FieldType,
    CoordinateSystemType,
)
from ...core.dtypes import FieldDataset

import logging
from warnings import warn

logger = logging.getLogger(__name__)


@dataclass
class RectWaveguide:
    """Dimensions in meters, band in Hz."""

    x: float  # m
    y: float  # m
    band: Tuple[float, float]  # Hz


def rect_far_field(
    ap_x: float,  # Cross-pol
    ap_y: float,  # Co-pol
    phi_sample_locs: NDArray,
    theta_sample_locs: NDArray,
    wavelength_array: float | NDArray,
    r_ff: float = 100,
    amplitude: float = 1.0,
    excitation: str = "te10",  # [te10, uniform]
    weights_only: bool = False,
):
    """Generate ideal rectangular aperture field.

    Based on derivation in [§12, 1].  It is assumed the E-field excitation is in the y-hat direction.

    Parameters
    ----------
    ap_x : float
        X-extent of the aperture (cross-pol) in meters
    ap_y : float
        Y-extent of the aperture (co-pol) in meters
    phi_sample_locs : NDArray
        Phi sample locations of the far-field in radians
    theta_sample_locs : NDArray
        Theta sample locations of the far-field in radians
    wavelength_array : float | NDArray
        Wavelengths to sample aperture at in meters
    r_ff : float, optional
        Far-field radius to compute field at in meters (important for absolute phase comparisons), by default 100 m
    amplitude : float, optional
        Maximum excitation amplitude in V, by default 1.0 V
    excitation : str, optional
        Aperture excitation mode. Must be either `uniform` or `te10`, by default `te10`
    weights_only : bool, optional
        Return only the real normalized weighting values, no phase or propagation loss due to Green's function

    Returns
    -------
    xr.Dataset if `weigths_only` is `False`
        Dataset containing "E" and "H" fields.
    NDArray if `weigths_only` is `True`
        2D matrix containing weighting values

    Raises
    ------
    NotImplementedError
        Excitation mode requested is not implementated.

    References
    ----------
    [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
        N.J: Wiley-Interscience, 2005.
    """
    frequency_array = np.array(1 / wavelength_array)

    # Create sampling grid
    theta_grid, phi_grid = np.meshgrid(theta_sample_locs, phi_sample_locs)
    phi_grid = phi_grid[:, :, np.newaxis]
    theta_grid = theta_grid[:, :, np.newaxis]

    e_0 = amplitude

    # Compute far-field constants
    wavelength_array = spc.c / frequency_array
    k_0 = 2.0 * np.pi / wavelength_array

    # Compute far-field distance based on aperture at spec. frequency
    d_2 = ap_x**2 + ap_y**2  # Maximum aperture extents, squared
    r_ff_min = 2.0 * d_2 / wavelength_array  # Far-field radius (m)

    if r_ff < r_ff_min:
        warn(
            f"Far-zone radius is {r_ff_min} m but {r_ff} m was given--far-field approximation is not valid.",
            RuntimeWarning,
        )

    # Constants from [Table 12.1, 1]

    x_ff = k_0 * ap_x / 2 * np.sin(theta_grid) * np.cos(phi_grid)
    y_ff = k_0 * ap_y / 2 * np.sin(theta_grid) * np.sin(phi_grid)

    if excitation == "uniform":
        cx = np.sinc(x_ff / np.pi)
        cy = np.sinc(y_ff / np.pi)
        e_theta = np.sin(phi_grid) * cx * cy
        e_phi = np.cos(theta_grid) * np.cos(phi_grid) * cx * cy
    elif excitation == "te10":
        cx = np.cos(x_ff) / (x_ff**2 - (np.pi / 2) ** 2)
        cy = np.sinc(y_ff / np.pi)
        e_theta = np.sin(phi_grid) * cx * cy
        e_phi = np.cos(theta_grid) * np.cos(phi_grid) * cx * cy
    else:
        raise NotImplementedError(f"Excitation mode {excitation} is not yet implemented.")

    e_field = np.stack([e_phi, e_theta])

    # Include Green's function weighting
    if not weights_only:
        greens_func_ff = np.exp(-1j * k_0 * r_ff) / (2.0 * np.pi * r_ff)
        c_ff = 1j * ap_x * ap_y * k_0 * e_0 * greens_func_ff
        e_field *= c_ff

        if excitation == "te10":
            e_field *= -np.pi / 2

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "phi": phi_sample_locs,
            "theta": theta_sample_locs,
        },
        frequency=frequency_array,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=DataSourceType.ANALYTIC,
    )

    return fields
