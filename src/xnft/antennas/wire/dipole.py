"""
Module providing dipole fields.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging

import numpy as np
import scipy.constants as spc

from ...common.enums import (
    CoordinateSystemType,
    FieldType,
)
from ...common.registry import registry
from ...common.types import FieldDataset

logger = logging.getLogger(__name__)

# Constants
eta = (spc.mu_0 / spc.epsilon_0) ** 0.5


def dipole_e(r, theta, phi, i_0=1, dipole_len=1.0, k=1):
    """Electric field of a finte dipole_length thin wire dipole for all space [§8.5.2A, 1].

    Parameters
    ----------
    r : Number, NDArray
        Field point radius.
    theta : Number, NDArray
        Field point theta (spherical).
    phi : Number, NDArray
        Field point phi (spherical).
    i_0 : int, optional
        Excitation current magnitude, by default 1
    dipole_len : float, optional
        Total length of dipole in meters, by default 1.0
    k : NDArray or int, optional
        Wavenumber in radians per meter, by default 1

    Returns
    -------
    xr.Dataset
        Field dataset with validated components and attributes

    References
    ----------
    [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
        N.J: Wiley-Interscience, 2005.

    """
    # logger.debug()

    # Cast k to ensure it's an NDArray
    k = np.atleast_1d(k)
    k_m = k[:, None, None]

    theta_m, phi_m = np.meshgrid(theta, phi, indexing="ij")

    x = r * np.sin(theta_m) * np.cos(phi_m)
    y = r * np.sin(theta_m) * np.sin(phi_m)
    z = r * np.cos(theta_m)

    rho_clip = (x**2 + y**2) ** 0.5

    R1 = (rho_clip**2 + (z - dipole_len / 2) ** 2) ** 0.5
    R2 = (rho_clip**2 + (z + dipole_len / 2) ** 2) ** 0.5

    const = 1.0j * eta * i_0 / (4.0 * np.pi)

    e_rho = (const / rho_clip) * (
        (z - dipole_len / 2) * np.exp(-1j * k_m * R1) / R1
        + (z + dipole_len / 2) * np.exp(-1j * k_m * R2) / R2
        - (2 * z) * np.cos(k_m * dipole_len / 2) * np.exp(-1j * k_m * r) / r
    )

    e_x = e_rho * np.cos(phi_m)

    e_y = e_rho * np.sin(phi_m)

    e_z = -const * (
        np.exp(-1j * k_m * R1) / R1
        + np.exp(-1j * k_m * R2) / R2
        - 2 * np.cos(k_m * dipole_len / 2) * np.exp(-1j * k_m * r) / r
    )

    e_field = np.stack([e_x, e_y, e_z], axis=-1)[:, None, :, :, :]

    freq_vec = k * spc.c / (2 * np.pi)

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "r": r,
            "phi": phi,
            "theta": theta,
        },
        frequency=freq_vec,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.NEAR,
        data_source=registry.data_sources.get("xnft.analytic"),
    )

    return fields


def dipole_e_far_field(theta, phi=0, r=1, i_0=1, dipole_len=1.0, k=1):
    """Far-field approximation of the electric field for a finite dipole_length thin wire dipole [§4.5.2, 1].

    Dipole oriented along the y-axis.

    Parameters
    ----------
    theta : Number, NDArray
        Field point theta (spherical).
    phi : Number, NDArray
        Field point phi (spherical). For dipole this parameter does not impact the field, but is included
        for completeness.
    r : Number, NDArray
        Field point radius.
    i_0 : int, optional
        Excitation current magnitude, by default 1
    dipole_len : float, optional
        Total length of dipole antenna in meters, by default 1.0
    k : NDArray or int, optional
        Wavenumber in radians per meter, by default 1

    Returns
    -------
    xr.Dataset
        Field dataset with validated components and attributes


    References
    ----------
    [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
        N.J: Wiley-Interscience, 2005.
    """
    k = np.atleast_1d(k)
    k_m = k[None, None, :]

    theta_m, phi_m = np.meshgrid(theta, phi, indexing="ij")

    theta_m = theta_m[..., None]
    phi_m = phi_m[..., None]

    # Compute theta component of E-field
    e_theta = (
        (1j * eta)
        * (i_0 * np.exp(-1j * k_m * r) / (2 * np.pi * r))
        * (
            (
                np.cos(k_m * dipole_len / 2 * np.cos(theta_m))
                - np.cos(k_m * dipole_len / 2)
            )
            / np.sin(theta_m)
        )
    )

    e_phi = np.zeros_like(e_theta)

    # Shape: (component, theta, phi, frequency)
    e_field = np.stack([e_theta, e_phi], axis=0)

    freq_vec = k * spc.c / (2 * np.pi)

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "theta": theta,
            "phi": phi,
        },
        frequency=freq_vec,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=registry.data_sources.get("xnft.analytic"),
    )

    return fields
