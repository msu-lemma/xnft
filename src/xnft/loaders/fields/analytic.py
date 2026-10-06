"""
Loader functions for ideal antenna model files.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging

import numpy as np
import scipy.constants as spc
import xarray as xr
import yaml

from ...antennas.aperture.rectangular import rect_e_far_field, rect_e_near_field
from ...antennas.wire.dipole import dipole_e, dipole_e_far_field
from ...common.enums import (
    DataPolarizationType,
    FieldType,
    PolarizationType,
    ScanType,
)
from ...common.registry import registry
from ...common.types import FileInfo

logger = logging.getLogger(__name__)


# === REGISTER LOADERS ===========================================================

# Register DataSource
ANALYTIC_SOURCE = registry.data_sources.register(
    id="xnft.analytic",
    display_name="Analytic Source",
)


@registry.loaders.fields.register(
    source=ANALYTIC_SOURCE,
    field_type=FieldType.NEAR,
    scan_type=ScanType.PLANAR,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".yaml",
)
def load_analytic_near_field_planar_yaml(file_list: list[FileInfo]) -> xr.Dataset:
    return load_analytic_yaml(
        file_list=file_list,
        field_type=FieldType.NEAR,
        scan_type=ScanType.PLANAR,
    )


@registry.loaders.fields.register(
    source=ANALYTIC_SOURCE,
    field_type=FieldType.NEAR,
    scan_type=ScanType.SPHERICAL,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".yaml",
)
def load_analytic_near_field_spherical_yaml(file_list: list[FileInfo]) -> xr.Dataset:
    return load_analytic_yaml(
        file_list=file_list,
        field_type=FieldType.NEAR,
        scan_type=ScanType.SPHERICAL,
    )


@registry.loaders.fields.register(
    source=ANALYTIC_SOURCE,
    field_type=FieldType.FAR,
    scan_type=ScanType.SPHERICAL,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".yaml",
)
def load_analytic_far_field_yaml(file_list: list[FileInfo]) -> xr.Dataset:
    return load_analytic_yaml(
        file_list=file_list,
        field_type=FieldType.FAR,
        scan_type=ScanType.SPHERICAL,
    )


# === YAML LOADERS ===========================================================


def load_analytic_yaml(
    file_list: list[FileInfo], field_type: FieldType, scan_type: ScanType
) -> xr.Dataset:
    """
    Generic analytic YAML loader based on simple description file.  Calls specific loaders for various scan type and field parameters.

    Parameters
    ----------
    file_path : List
        List of FieldInfo objects pointing to the near-field theory files.

    TODO: add further arguments

    Returns
    -------
    xr.Dataset
        Field dataset with validated components and attributes

    """

    if len(file_list) != 1:
        raise ValueError(f"Analytic loader accepts exactly one file. Got: {file_list}")
    if file_list[0].polarization != {
        PolarizationType.CO_POL,
        PolarizationType.CROSS_POL,
    }:
        raise ValueError(
            "Analytic loader only accepts files containing both co-pol and cross-pol."
        )

    file_path = file_list[0].path
    with open(file_path, "r", encoding="utf-8") as file:
        fd = yaml.safe_load(file)

    # Call specific loader based on antenna type
    antenna_type = fd["antenna"]["type"]
    if antenna_type == "rectangular_aperture":
        fields = load_rect_aperture_yaml(fd, field_type=field_type, scan_type=scan_type)
    elif antenna_type == "dipole":
        fields = load_dipole_yaml(fd, field_type=field_type, scan_type=scan_type)
    else:
        raise NotImplementedError(f"Antenna type {antenna_type} not implemented.")

    return fields


def load_rect_aperture_yaml(fd, field_type, scan_type):

    # Read common parameters
    freq_sample_vec = np.array(fd["samples"]["frequency"])

    # Read excitation parameters
    excitation = fd["antenna"]["excitation"]["distribution"]
    e_0 = fd["antenna"]["excitation"]["e_0"]

    # Get antenna aperture extents
    aperture_x_min = fd["antenna"]["x"]["bounds"][0]
    aperture_x_max = fd["antenna"]["x"]["bounds"][1]
    aperture_y_min = fd["antenna"]["y"]["bounds"][0]
    aperture_y_max = fd["antenna"]["y"]["bounds"][1]

    if field_type == FieldType.NEAR:
        x_max = fd["samples"]["near_field"]["x"]["bounds"][1]
        x_min = fd["samples"]["near_field"]["x"]["bounds"][0]
        x_size = fd["samples"]["near_field"]["x"]["size"]

        y_max = fd["samples"]["near_field"]["y"]["bounds"][1]
        y_min = fd["samples"]["near_field"]["y"]["bounds"][0]
        y_size = fd["samples"]["near_field"]["y"]["size"]

        x_sample_vec = np.linspace(x_min, x_max, x_size)
        y_sample_vec = np.linspace(y_min, y_max, y_size)
        z_sample_vec = np.array([0], np.float64)

        fields = rect_e_near_field(
            ap_x=[aperture_x_min, aperture_x_max],
            ap_y=[aperture_y_min, aperture_y_max],
            x_sample_vec=x_sample_vec,
            y_sample_vec=y_sample_vec,
            z_sample_vec=z_sample_vec,
            freq_sample_vec=freq_sample_vec,
            amplitude=e_0,
            excitation=excitation,
        )

    elif field_type == FieldType.FAR:
        # Get far-field sample locations
        theta_max = fd["samples"]["far_field"]["theta"]["bounds"][1]
        theta_min = fd["samples"]["far_field"]["theta"]["bounds"][0]
        theta_num_samples = fd["samples"]["far_field"]["theta"]["size"]

        phi_max = fd["samples"]["far_field"]["phi"]["bounds"][1]
        phi_min = fd["samples"]["far_field"]["phi"]["bounds"][0]
        phi_num_samples = fd["samples"]["far_field"]["phi"]["size"]

        theta_sample_location_array = (
            np.linspace(theta_min, theta_max, theta_num_samples) * np.pi / 180
        )
        phi_sample_location_array = (
            np.linspace(phi_min, phi_max, phi_num_samples) * np.pi / 180
        )

        ap_x = aperture_x_max - aperture_x_min
        ap_y = aperture_y_max - aperture_y_min

        # Compute far-field constants
        wavelength = spc.c / freq_sample_vec

        # Compute far-field distance based on aperture at spec. frequency
        d_2 = ap_x**2 + ap_y**2  # Maximum aperture extents, squared
        r_ff = 2.0 * d_2 / wavelength  # Far-field radius (m)

        fields = rect_e_far_field(
            ap_x=ap_x,
            ap_y=ap_y,
            wavelength_array=wavelength,
            theta_sample_vec=theta_sample_location_array,
            phi_sample_vec=phi_sample_location_array,
            r_ff=r_ff,
            amplitude=e_0,
            excitation=excitation,
        )
    else:
        raise ValueError(
            f"Field type {field_type} is not valid. Must be FieldType.NEAR or FieldType.FAR"
        )

    return fields


def load_dipole_yaml(fd, field_type, scan_type):
    r = fd["samples"]["near_field"]["r"]

    phi_max = np.deg2rad(fd["samples"]["near_field"]["phi"]["bounds"][1])
    phi_min = np.deg2rad(fd["samples"]["near_field"]["phi"]["bounds"][0])
    phi_size = fd["samples"]["near_field"]["phi"]["size"]

    theta_max = np.deg2rad(fd["samples"]["near_field"]["theta"]["bounds"][1])
    theta_min = np.deg2rad(fd["samples"]["near_field"]["theta"]["bounds"][0])
    theta_size = fd["samples"]["near_field"]["theta"]["size"]

    r_sample_vec = np.array([r], np.float64)
    phi_sample_vec = np.linspace(phi_min, phi_max, phi_size)
    theta_sample_vec = np.linspace(theta_min, theta_max, theta_size)
    freq_sample_vec = np.array(fd["samples"]["frequency"])
    wavenumber_vec = 2 * np.pi * freq_sample_vec / spc.c

    excitation_current = fd["antenna"]["excitation"]["i_0"]

    length = fd["antenna"]["bounds"]

    if field_type == FieldType.NEAR:
        # Dipole electric fields everywhere
        dipole_field = dipole_e
    elif field_type == FieldType.FAR:
        # Dipole electric far-field approximation
        dipole_field = dipole_e_far_field
    else:
        raise ValueError(
            f"Field type {field_type} is not valid. Must be FieldType.NEAR or FieldType.FAR"
        )

    args = {
        "r": r_sample_vec,
        "theta": theta_sample_vec,
        "phi": phi_sample_vec,
        "i_0": excitation_current,
        "dipole_len": length,
        "k": wavenumber_vec,
    }

    # logger.debug(f"{args=}")

    fields = dipole_field(**args)

    return fields
