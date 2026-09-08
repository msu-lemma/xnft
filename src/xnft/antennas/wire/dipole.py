"""
Module providing dipole fields.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import numpy as np
import scipy.constants as spc

from ...common.enums import (
    CoordinateSystemType,
    DataSourceType,
    FieldType,
)
from ...common.types import FieldDataset

# Constants
eta = (spc.mu_0 / spc.epsilon_0) ** 0.5


def dipole_e(r, theta, phi, i_0=1, len=0.5, k=1):
    """Electric field of a finte length thin wire dipole for all space [§8.5.2A, 1].

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
    len : float, optional
        Total length of dipole in meters, by default 0.5
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

    # Cast k to ensure it's an NDArray
    k = np.array(k)

    theta_m, phi_m = np.meshgrid(theta, phi, indexing="xy")

    x = r * np.sin(theta_m) * np.cos(phi_m)
    y = r * np.sin(theta_m) * np.sin(phi_m)
    z = r * np.cos(theta_m)

    rho = (x**2 + y**2) ** 0.5

    R1 = (rho**2 + (z - len / 2) ** 2) ** 0.5
    R2 = (rho**2 + (z + len / 2) ** 2) ** 0.5

    const = 1.0j * eta * i_0 / (4.0 * np.pi)

    e_rho = (const / rho) * (
        (z - len / 2) * np.exp(-1j * k[:, None, None] * R1) / R1
        + (z + len / 2) * np.exp(-1j * k[:, None, None] * R2) / R2
        - 2
        * z
        * np.cos(k[:, None, None] * len / 2)
        * np.exp(-1j * k[:, None, None] * r)
        / r
    )

    e_x = e_rho * np.cos(phi_m)

    e_y = e_rho * np.sin(phi_m)

    e_z = -const * (
        np.exp(-1j * k[:, None, None] * R1) / R1
        + np.exp(-1j * k[:, None, None] * R2) / R2
        - 2
        * np.cos(k[:, None, None] * len / 2)
        * np.exp(-1j * k[:, None, None] * r)
        / r
    )

    e_field = np.stack([e_x, e_y, e_z]).reshape((3, 1, *theta_m.shape, 3))

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
        data_source=DataSourceType.ANALYTIC,
    )

    return fields


def dipole_e_far_field(theta, phi=0, r=1, i_0=1, len=0.5, k=1):
    """Far-field approximation of the electric field for a finite length thin wire dipole [§4.5.2, 1].

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
    len : float, optional
        Total length of dipole antenna in meters, by default 0.5
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
    # Compute theta component of E-field
    e_theta = (
        (1j * eta)
        * (i_0 * np.exp(-1j * k[:, None, None] * r) / (2 * np.pi * r))
        * (
            (
                np.cos(k[:, None, None] * len / 2 * np.cos(theta))
                - np.cos(k[:, None, None] * len / 2)
            )
            / np.sin(theta)
        )
    )

    # Convert to cartesian vector components for uniform reporting to xNFT
    theta_m, phi_m = np.meshgrid(theta, phi, indexing="xy")
    e_x = np.cos(theta_m) * np.cos(phi_m) * e_theta
    e_y = np.cos(theta_m) * np.sin(phi_m) * e_theta
    e_z = -np.sin(theta_m) * e_theta

    e_field = np.stack([e_x, e_y, e_z]).reshape((3, 1, *theta_m.shape, 3))

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
        data_source=DataSourceType.ANALYTIC,
    )

    return fields
