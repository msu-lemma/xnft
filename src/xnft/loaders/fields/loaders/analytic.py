"""
Loader functions for analytic "ideal aperture" files.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from typing import List

import yaml
import numpy as np
import xarray as xr

import scipy.constants as spc

from ..field_loader_registry import field_loader_registry
from ....core.enums import (
    DataSourceType,
    FieldType,
    CoordinateSystemType,
    PolarizationType,
    DataPolarizationType,
    Units
)
from ....core.types import FileInfo
from ....core.dtypes import FieldDataset

from ....core.apertures.rectangular import rect_far_field

logger = logging.getLogger(__name__)


@field_loader_registry.register(
    source=DataSourceType.ANALYTIC,
    field=FieldType.NEAR,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".yaml",
)
def load_analytic_near_field_yaml(file_list: List[FileInfo]) -> xr.Dataset:
    """
    Generate analytic near-field based on simple description file.

    Parameters
    ----------
    file_path : List
        List of FieldInfo objects pointing to the near-field theory files.

    Returns
    -------
    xr.Dataset
        Dataset containing "E" and "H" fields.

    TODO
    ----
    1. Refactor near-field to core.apertures.rectangular rect_near_field()
    """

    if len(file_list) != 1:
        raise ValueError(f"Analytic loader accepts exactly one file. Got: {file_list}")

    if file_list[0].polarization != {PolarizationType.CO_POL, PolarizationType.CROSS_POL}:
        raise ValueError("Analytic loader only accepts files containing both co-pol and cross-pol.")

    file_path = file_list[0].path

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

    e_x = e_z = np.zeros((x_size, y_size, 1, sample_frequency_array.size), np.complex128)
    e_y = e_0 * np.ones((x_size, y_size, 1, sample_frequency_array.size), np.complex128)
    # h_x = h_y = h_z = np.zeros((x_size, y_size, 1, sample_frequency_array.size), np.complex128)

    yy, xx = np.meshgrid(y_sample_location_array, x_sample_location_array)

    # Get antenna aperture extents

    aperture_x_min = fd["antenna"]["x"]["length"][0]
    aperture_x_max = fd["antenna"]["x"]["length"][1]
    aperture_y_min = fd["antenna"]["y"]["length"][0]
    aperture_y_max = fd["antenna"]["y"]["length"][1]

    cond = (
        (xx <= aperture_x_max)
        & (xx >= aperture_x_min)
        & (yy <= aperture_y_max)
        & (yy >= aperture_y_min)
    )

    e_y *= np.where(cond, 1.0, 0.0)[:, :, None, None]

    excitation_distribution = fd["antenna"]["excitation"]["distribution"]

    if excitation_distribution == "uniform":
        pass  # Nothing needed for uniform
    elif excitation_distribution == "te10":
        # Taper fields based on TE-10 mode
        e_y *= np.cos(np.pi / (aperture_x_max - aperture_x_min) * xx)[:, :, None, None]
    else:
        raise NotImplementedError(
            f"Excitation distribution {excitation_distribution} is not yet " "implemented."
        )

    e_field = np.stack([e_x, e_y, e_z])
    # h_field = np.stack([h_x, h_y, h_z])

    fields = FieldDataset.create(
        e_field=e_field,
        # h_field=h_field,
        spatial_coords={
            "x": x_sample_location_array,
            "y": y_sample_location_array,
            "z": z_sample_location_array,
        },
        frequency=sample_frequency_array,
        coordinate_system=CoordinateSystemType.CARTESIAN,
        field_type=FieldType.NEAR,
        data_source=DataSourceType.ANALYTIC
    )

    return fields


@field_loader_registry.register(
    source=DataSourceType.ANALYTIC,
    field=FieldType.FAR,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".yaml",
)
def load_theory_far_field_yaml(file_list: List[FileInfo]) -> xr.Dataset:
    """
    Generate theoretical far-field based on simple description file.

    Parameters
    ----------
    file_path : List
        List of FieldInfo objects pointing to the near-field theory files.

    Returns
    -------
    xr.Dataset
        Dataset containing "E" and "H" fields.
    """
    if len(file_list) != 1:
        raise ValueError(f"Analytic loader accepts exactly one file. Got: {file_list}")

    if file_list[0].polarization != {PolarizationType.CO_POL, PolarizationType.CROSS_POL}:
        raise ValueError("Analytic loader only accepts files containing both co-pol and cross-pol.")

    file_path = file_list[0].path

    with open(file_path, "r", encoding="utf-8") as file:
        fd = yaml.safe_load(file)

    phi_max = fd["samples"]["far_field"]["phi"]["length"][1]
    phi_min = fd["samples"]["far_field"]["phi"]["length"][0]
    phi_num_samples = fd["samples"]["far_field"]["phi"]["size"]

    theta_max = fd["samples"]["far_field"]["theta"]["length"][1]
    theta_min = fd["samples"]["far_field"]["theta"]["length"][0]
    theta_num_samples = fd["samples"]["far_field"]["theta"]["size"]

    phi_sample_location_array = np.linspace(phi_min, phi_max, phi_num_samples) * np.pi / 180
    theta_sample_location_array = np.linspace(theta_min, theta_max, theta_num_samples) * np.pi / 180
    sample_frequency_array = np.array(fd["samples"]["frequency"])

    ap_x_min = fd["antenna"]["x"]["length"][0]
    ap_x_max = fd["antenna"]["x"]["length"][1]
    ap_y_min = fd["antenna"]["y"]["length"][0]
    ap_y_max = fd["antenna"]["y"]["length"][1]

    ap_x = ap_x_max - ap_x_min
    ap_y = ap_y_max - ap_y_min

    print(f'{ap_x=}')
    print(f'{ap_y=}')

    # Compute far-field constants
    wavelength = spc.c / sample_frequency_array

    # Compute far-field distance based on aperture at spec. frequency
    d_2 = ap_x**2 + ap_y**2  # Maximum aperture extents, squared
    r_ff = 2.0 * d_2 / wavelength  # Far-field radius (m)

    fields = rect_far_field(
        ap_x=ap_x,
        ap_y=ap_y,
        wavelength_array=wavelength,
        phi_sample_vec=phi_sample_location_array,
        theta_sample_vec=theta_sample_location_array,
        r_ff=r_ff,
        amplitude=fd["antenna"]["excitation"]["e_0"],
        excitation=fd["antenna"]["excitation"]["distribution"],
    )

    return fields
