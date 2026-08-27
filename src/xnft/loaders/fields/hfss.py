"""
Loader functions for Ansys HFSS files.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
import io
from typing import List
from pathlib import Path

import numpy as np
import xarray as xr

from .field_loader_registry import field_loader_registry
from ...core.enums import (
    DataSourceType,
    FieldType,
    PolarizationType,
    CoordinateSystemType,
    DataPolarizationType,
    ScanType,
)
from ...core.types import FileInfo
from ...core.dtypes import FieldDataset

logger = logging.getLogger(__name__)


@field_loader_registry.register(
    source=DataSourceType.HFSS,
    field=FieldType.NEAR,
    scan=ScanType.PLANAR,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".nfd",
)
def load_hfss_near_field_ndf(file_list: List[FileInfo]) -> xr.Dataset:
    """
    Load near-field file data.

    Parameters
    ----------
    file_list : List[FileInfo]
        List of FieldInfo objects pointing to the near-field data files (.nfd).

    Returns
    -------
    xarray.Dataset
        Dataset containing "E" and "H" fields.
    """
    if len(file_list) != 1:
        raise ValueError("HFSS .nfd loader accepts exactly one file.")

    if file_list[0].polarization != {PolarizationType.CO_POL, PolarizationType.CROSS_POL}:
        raise ValueError(
            "HFSS .nfd loader only accepts files containing both co-pol and cross-pol."
        )

    # Ensure file_list.path is a Path
    file_path = Path(file_list[0].path)

    logger.debug(f'{file_path=}')

    if file_path.suffix != ".nfd":
        raise TypeError(f"File type must be '.nfd', got '{file_path.suffix}'.")

    logger.debug('Loading HFSS near-field file "%s".', file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        # Initialize temporary data variables
        x_list = []
        y_list = []
        z_list = []
        ex_list = []
        ey_list = []
        ez_list = []
        hx_list = []
        hy_list = []
        hz_list = []
        frequency_list = []

        # Initialize parsing variables
        num_frequencies = None
        current_frequency = None

        # Read over each line of file and build data lists
        for line in file:
            # Skip comments
            if line[0] == "#":
                logger.debug("Skipping comment line: %s", line.strip())
                continue

            # Find frequency content
            if line[0] == "F":  # Frequency content lines start with 'F'
                if "Frequencies" in line and num_frequencies is None:
                    num_frequencies = int(line.split(" ")[1])
                    logger.debug("Found num_frequencies = %i", num_frequencies)
                if "Frequency" in line:
                    current_frequency = float(line.split(" ")[1])
                    logger.debug("Found current_frequency = %e Hz", current_frequency)
            else:  # all other lines are regularly formatted data
                tokens = [float(x) for x in line.split(",")]
                # logger.debug(tokens)
                frequency_list.append(current_frequency)
                x_list.append(tokens[1])
                y_list.append(tokens[2])
                z_list.append(tokens[3])
                ex_list.append(tokens[4] + 1j * tokens[5])
                ey_list.append(tokens[6] + 1j * tokens[7])
                ez_list.append(tokens[8] + 1j * tokens[9])
                hx_list.append(tokens[10] + 1j * tokens[11])
                hy_list.append(tokens[12] + 1j * tokens[13])
                hz_list.append(tokens[14] + 1j * tokens[15])

    # === Post-process NFD File Data ===

    # Get unique x, y, and z sample location values
    x_sample_location_array = np.sort(np.array(list(set(x_list))))
    y_sample_location_array = np.sort(np.array(list(set(y_list))))
    z_sample_location_array = np.sort(np.array(list(set(z_list))))
    sample_frequency_array = np.sort(np.array(list(set(frequency_list))))

    logger.debug(
        "Sample location array shape: (x:%d, y:%d, z:%d, freq:%d)",
        x_sample_location_array.size,
        y_sample_location_array.size,
        z_sample_location_array.size,
        sample_frequency_array.size,
    )

    # Allocate new data array in multidimensional format
    fields_shape = (
        3,  # 3 for x,y,z component of the field
        x_sample_location_array.size,
        y_sample_location_array.size,
        z_sample_location_array.size,
        sample_frequency_array.size,
    )
    e_field = np.empty(fields_shape, dtype=np.complex128)
    h_field = np.empty(fields_shape, dtype=np.complex128)

    # Re-run over data and re-organize measured data into appropriate
    # format (x,y,z,frequency)
    for x_loc, y_loc, z_loc, freq, ex, ey, ez, hx, hy, hz in zip(
        x_list,
        y_list,
        z_list,
        frequency_list,
        ex_list,
        ey_list,
        ez_list,
        hx_list,
        hy_list,
        hz_list,
    ):
        x_index = np.where(x_sample_location_array == x_loc)[0][0]
        y_index = np.where(y_sample_location_array == y_loc)[0][0]
        z_index = np.where(z_sample_location_array == z_loc)[0][0]
        freq_index = np.where(sample_frequency_array == freq)[0][0]

        e_field[:, x_index, y_index, z_index, freq_index] = ex, ey, ez
        h_field[:, x_index, y_index, z_index, freq_index] = hx, hy, hz

    fields = FieldDataset.create(
        e_field=e_field,
        h_field=h_field,
        spatial_coords={
            "x": x_sample_location_array,
            "y": y_sample_location_array,
            "z": z_sample_location_array,
        },
        frequency=sample_frequency_array,
        coordinate_system=CoordinateSystemType.CARTESIAN,
        field_type=FieldType.NEAR,
        data_source=DataSourceType.HFSS
    )

    fields_buffer = io.StringIO()
    fields.info(buf=fields_buffer)
    logger.debug(fields_buffer.getvalue())

    return fields


@field_loader_registry.register(
    source=DataSourceType.HFSS,
    field=FieldType.FAR,
    scan=ScanType.SPHERICAL,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".ffd",
)
def load_hfss_far_field_ffd(file_list: List[FileInfo]) -> xr.Dataset:
    """
    Load far-field file data.

    Parameters
    ----------
    file_list : List[FileInfo]
        List of FieldInfo objects pointing to the near-field data files (.nfd).

    Returns
    -------
    xarray.Dataset
        Dataset containing "E" and "H" fields.
    """
    if len(file_list) != 1:
        raise ValueError("HFSS .ffd loader accepts exactly one file.")

    if file_list[0].polarization != {PolarizationType.CO_POL, PolarizationType.CROSS_POL}:
        raise ValueError(
            "HFSS .ffd loader only accepts files containing both co-pol and cross-pol."
        )

    # Ensure file_list.path is a Path
    file_path = Path(file_list[0].path)

    if file_path.suffix != ".ffd":
        raise TypeError(f"File type must be '.ffd', got '{file_path.suffix}'.")

    logger.debug('Loading HFSS far-field file "%s".', file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        # Initialize parsing variables
        num_frequencies = None
        current_frequency = None
        # Will increment to 0 after first frequency is encountered
        frequency_index = -1

        # Data index -- used to count sample row number for a given frequency
        data_index = -1

        # Read over each line of file and build data lists
        for line_idx, line in enumerate(file):
            # Skip comments
            if line[0] == "#":
                logger.debug("Skipping comment line: %s", line.strip())
                continue

            # Extract phi/theta sample locations (first two rows)
            # Elevation (Theta)
            elif line_idx == 0:
                theta_start_deg, theta_stop_deg, theta_num_steps = [
                    float(x.strip()) for x in line.split(" ")
                ]
                theta_sample_location_array = np.radians(
                    np.linspace(theta_start_deg, theta_stop_deg, int(theta_num_steps))
                )
            # Azimuth (Phi)
            elif line_idx == 1:
                phi_start_deg, phi_stop_deg, phi_num_steps = [float(x) for x in line.split(" ")]
                phi_sample_location_array = np.radians(
                    np.linspace(phi_start_deg, phi_stop_deg, int(phi_num_steps))
                )

            # Extract number of frequencies from header
            elif line_idx == 2:
                num_frequencies = int(line.split(" ")[1])
                logger.debug("Found num_frequencies = %i", num_frequencies)

                # Line 2 is the end of the header, so we will create the data
                # arrays now
                fields_shape = (
                    2,  # 2 for phi, theta components of the field
                    phi_sample_location_array.size,
                    theta_sample_location_array.size,
                    num_frequencies,
                )
                logger.debug("fields_shape: %s", fields_shape)
                e_field = np.empty(fields_shape, dtype=np.complex128)
                sample_frequency_array = np.empty(num_frequencies, np.float64)

            # Find frequency content
            elif line[0] == "F":  # Frequency content lines start with 'F'
                if "Frequency" in line:
                    # Increment frequency index
                    frequency_index += 1

                    current_frequency = float(line.split(" ")[1])
                    sample_frequency_array[frequency_index] = current_frequency
                    logger.debug("Found current_frequency = %e Hz", current_frequency)

                    # Reset data_index to -1 (counts sample offset for a
                    # given frequency), increments at end of loop
                    data_index = -1

            else:  # all other lines are regularly formatted data
                tokens = [float(x) for x in line.split(" ")]

                # Format: magnitude * exp(j * angle)
                e_phi = tokens[2] + 1j * tokens[3]
                e_theta = tokens[0] + 1j * tokens[1]

                phi_index = int(data_index % phi_num_steps)
                theta_index = int(data_index // phi_num_steps)

                e_field[:, phi_index, theta_index, frequency_index] = (
                    e_phi,
                    e_theta,
                )

            # Increment the data row index for current frequency
            data_index += 1

    # === Post-process FFD File Data ===

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "theta": theta_sample_location_array,
            "phi": phi_sample_location_array,
        },
        frequency=sample_frequency_array,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=DataSourceType.HFSS
    )

    fields_buffer = io.StringIO()
    fields.info(buf=fields_buffer)
    logger.debug(fields_buffer.getvalue())

    return fields
