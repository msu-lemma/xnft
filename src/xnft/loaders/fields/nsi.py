"""
Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import io
import logging
from pathlib import Path

import numpy as np
import xarray as xr

from ...common.enums import (
    CoordinateSystemType,
    DataPolarizationType,
    DataSourceType,
    FieldType,
    PolarizationType,
    ScanType,
)
from ...common.types import FieldDataset, FileInfo
from ..registry import field_loader_registry

logger = logging.getLogger(__name__)


@field_loader_registry.register(
    source=DataSourceType.NSI_MEAS,
    field=FieldType.NEAR,
    scan=ScanType.SPHERICAL,
    data_polarization=DataPolarizationType.COMBO_POL,
    extension=".ffd",
)
def load_hfss_far_field_ffd(file_list: list[FileInfo]) -> xr.Dataset:
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

    if file_list[0].polarization != {
        PolarizationType.CO_POL,
        PolarizationType.CROSS_POL,
    }:
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
                phi_start_deg, phi_stop_deg, phi_num_steps = [
                    float(x) for x in line.split(" ")
                ]
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
        data_source=DataSourceType.HFSS,
    )

    fields_buffer = io.StringIO()
    fields.info(buf=fields_buffer)
    logger.debug(fields_buffer.getvalue())

    return fields
