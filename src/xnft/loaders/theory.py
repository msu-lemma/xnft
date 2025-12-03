"""
Loader functions for 'theory' files.

Theory files contain information to generate a theoretical ideal aperture [§12, 1].

[1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken, N.J: Wiley-Interscience, 2005.
"""

from pathlib import Path
import logging

import yaml
import pandas as pd
import numpy as np
import xarray as xr

import scipy.constants as spc

from .file_registry import registry


logger = logging.getLogger(__name__)


@registry.register(source="theory", field="near", extension=".yaml")
def load_theory_near_field_yaml(file_path: Path) -> xr.Dataset:
    """
    Generate theoretical near-field based on simple description file.

    Parameters
    ----------
    file_path : Path
        Path to theory description file.

    Returns
    -------
    xr.Dataset
        Dataset containing "E" and "H" fields.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        fd = yaml.safe_load(file)

    x_max = fd["samples"]["near_field"]["x"]["length"][1]
    x_min = fd["samples"]["near_field"]["x"]["length"][0]
    x_size = fd["samples"]["near_field"]["x"]["size"]

    y_max = fd["samples"]["near_field"]["y"]["length"][1]
    y_min = fd["samples"]["near_field"]["y"]["length"][0]
    y_size = fd["samples"]["near_field"]["y"]["size"]

    x_sample_location_array = np.linspace(x_min, x_max, x_size)
    y_sample_location_array = np.linspace(y_min, y_max, y_size)
    z_sample_location_array = np.array([0], np.float64)
    sample_frequency_array = np.array(fd["samples"]["frequency"])

    # Generate excitation

    e_0 = fd["antenna"]["excitation"]["e_0"]

    e_x = e_z = np.zeros(
        (x_size, y_size, 1, sample_frequency_array.size), np.float64
    )
    e_y = e_0 * np.ones(
        (x_size, y_size, 1, sample_frequency_array.size), np.float64
    )

    yy, xx = np.meshgrid(y_sample_location_array, x_sample_location_array)

    # Get antenna aperture extents

    aperture_x_min = fd["antenna"]["x"]["length"][0]
    aperture_x_max = fd["antenna"]["x"]["length"][1]
    aperture_y_min = fd["antenna"]["y"]["length"][0]
    aperture_y_max = fd["antenna"]["y"]["length"][1]

    cond = (
        (xx < aperture_x_max)
        & (xx > aperture_x_min)
        & (yy < aperture_y_max)
        & (yy > aperture_y_min)
    )

    e_y *= np.where(cond, 1.0, 0.0)[:, :, None, None]

    excitation_distribution = fd["antenna"]["excitation"]["distribution"]

    if excitation_distribution == "uniform":
        pass  # Nothing needed for uniform
    elif excitation_distribution == "te10":
        # Taper fields based on TE-10 mode
        e_y *= np.cos(np.pi / (aperture_x_max - aperture_x_min) * xx)[
            :, :, None, None
        ]
    else:
        raise NotImplementedError(
            f"Excitation distribution {excitation_distribution} is not yet implemented."
        )

    e_field = np.stack([e_x, e_y, e_z])

    # TODO / FIXME
    h_field = e_field

    fields = xr.Dataset(
        {
            "E": (
                ("component", "x", "y", "z", "frequency"),
                e_field,
                {"Units": "V/m"},
            ),
            "H": (
                ("component", "x", "y", "z", "frequency"),
                h_field,
                {"Units": "A/m"},
            ),
        },
        coords={
            "component": ["x", "y", "z"],
            "x": x_sample_location_array,
            "y": y_sample_location_array,
            "z": z_sample_location_array,
            "frequency": sample_frequency_array,
        },
    )

    return fields


@registry.register(source="theory", field="far", extension=".yaml")
def load_theory_far_field_yaml(file_path: Path) -> xr.Dataset:
    """
    Generate theoretical far-field based on simple description file.

    Parameters
    ----------
    file_path : Path
        Path to theory description file.

    Returns
    -------
    xr.Dataset
        Dataset containing "E" and "H" fields.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        fd = yaml.safe_load(file)

    phi_max = fd["samples"]["far_field"]["phi"]["length"][1]
    phi_min = fd["samples"]["far_field"]["phi"]["length"][0]
    phi_size = fd["samples"]["far_field"]["phi"]["size"]

    theta_max = fd["samples"]["far_field"]["theta"]["length"][1]
    theta_min = fd["samples"]["far_field"]["theta"]["length"][0]
    theta_size = fd["samples"]["far_field"]["theta"]["size"]

    phi_sample_location_array = (
        np.linspace(phi_min, phi_max, phi_size) * np.pi / 180
    )
    theta_sample_location_array = (
        np.linspace(theta_min, theta_max, theta_size) * np.pi / 180
    )
    sample_frequency_array = np.array(fd["samples"]["frequency"])

    ap_x_min = fd["antenna"]["x"]["length"][0]
    ap_x_max = fd["antenna"]["x"]["length"][1]
    ap_y_min = fd["antenna"]["y"]["length"][0]
    ap_y_max = fd["antenna"]["y"]["length"][1]

    ap_x = ap_x_max - ap_x_min
    ap_y = ap_y_max - ap_y_min

    # Create sampling grid

    theta_grid, phi_grid = np.meshgrid(
        theta_sample_location_array, phi_sample_location_array
    )
    phi_grid = phi_grid[:, :, np.newaxis]
    theta_grid = theta_grid[:, :, np.newaxis]

    e_0 = fd["antenna"]["excitation"]["e_0"]

    # Compute far-field constants
    wavelength = spc.c / sample_frequency_array
    k_0 = 2.0 * np.pi / wavelength
    eta = (spc.mu_0 / spc.epsilon_0) ** 0.5

    # Compute far-field distance based on aperture at spec. frequency
    d_2 = ap_x**2 + ap_y**2  # Maximum aperture extents, squared
    r_ff = 2.0 * d_2 / wavelength  # Far-field radius (m)

    # Constants from [Table 12.2, 1]

    c_ff = 1j * ap_x * ap_y * k_0 * e_0
    greens_func_ff = np.exp(-1j * k_0 * r_ff) / (2.0 * np.pi * r_ff)
    c_ff *= greens_func_ff

    x_ff = k_0 * ap_x / 2 * np.sin(theta_grid) * np.cos(phi_grid)
    y_ff = k_0 * ap_y / 2 * np.sin(theta_grid) * np.sin(phi_grid)

    excitation_distribution = fd["antenna"]["excitation"]["distribution"]

    if excitation_distribution == "uniform":
        e_theta = (
            c_ff
            * np.sin(phi_grid)
            * np.sinc(x_ff / np.pi)
            * np.sinc(y_ff / np.pi)
        )
        e_phi = (
            c_ff
            * np.cos(theta_grid)
            * np.cos(phi_grid)
            * np.sinc(x_ff / np.pi)
            * np.sinc(y_ff / np.pi)
        )
    elif excitation_distribution == "te10":
        e_theta = (
            -np.pi
            / 2
            * c_ff
            * np.sin(phi_grid)
            * np.cos(x_ff)
            / (x_ff**2 - (np.pi / 2) ** 2)
            * np.sinc(y_ff / np.pi)
        )
        e_phi = (
            -np.pi
            / 2
            * c_ff
            * np.cos(theta_grid)
            * np.cos(phi_grid)
            * np.cos(x_ff)
            / (x_ff**2 - (np.pi / 2) ** 2)
            * np.sinc(y_ff / np.pi)
        )
    else:
        raise NotImplementedError(
            f"Excitation distribution {excitation_distribution} is not yet implemented."
        )

    h_theta = -e_phi / eta
    h_phi = e_theta / eta

    e_field = np.stack([e_phi, e_theta])
    h_field = np.stack([h_phi, h_theta])

    fields = xr.Dataset(
        {
            "E": (
                ("component", "phi", "theta", "frequency"),
                e_field,
                {"Units": "V/m"},
            ),
            "H": (
                ("component", "phi", "theta", "frequency"),
                h_field,
                {"Units": "A/m"},
            ),
        },
        coords={
            "component": ["phi", "theta"],
            "phi": phi_sample_location_array,
            "theta": theta_sample_location_array,
            "frequency": sample_frequency_array,
        },
    )

    return fields
