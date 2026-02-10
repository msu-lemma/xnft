"""
Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from pathlib import Path
import logging
import h5py

import pandas as pd
import numpy as np
import xarray as xr
import scipy.constants as spc

from .file_registry import registry
from ..core.types import DataSourceType, FieldType, CoordinateSystem


logger = logging.getLogger(__name__)

@registry.register(
    source=DataSourceType.LEMMA, field=FieldType.NEAR, extension=".h5"
)
def load_lemma_h5(file_path: Path) -> xr.Dataset:
    POINTS_PER_METER = 200_000

    # Open file
    with h5py.File(file_path, 'r') as dataset:
        sample_frequencies = dataset['f'][()][0]
        sample_locations = dataset['points'][()] / POINTS_PER_METER
        x_locs = sample_locations[:, 0]
        y_locs = sample_locations[:, 2]
        z_locs = sample_locations[:, 1] + 0.069

        # s11 = dataset['S11real'][()] + 1.0j * dataset['S11imag'][()]
        # s12 = dataset['S12real'][()] + 1.0j * dataset['S12imag'][()]
        s21 = dataset['S21real'][()] + 1.0j * dataset['S21imag'][()]
        # s22 = dataset['S22real'][()] + 1.0j * dataset['S22imag'][()]

    x_list = x_locs.tolist()
    y_list = y_locs.tolist()
    z_list = z_locs.tolist()

    frequency_list = sample_frequencies.tolist()
    
    # TODO: Improve E field estimate
    # TODO: Need to add x, and y field components (from separate files?)
    # ex_list = (s21 + s12)/2
    ex_list = s21 
    ey_list = np.zeros_like(s21)
    ez_list = np.zeros_like(s21)

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

    # Find to insert field values in e_field array
    x_idx = np.searchsorted(x_sample_location_array, x_locs)
    y_idx = np.searchsorted(y_sample_location_array, y_locs)
    z_idx = np.searchsorted(z_sample_location_array, z_locs)

    for f_idx in range(sample_frequencies.size):
        e_field[0, x_idx, y_idx, z_idx, f_idx] = ex_list[:, f_idx]
        e_field[1, x_idx, y_idx, z_idx, f_idx] = ey_list[:, f_idx]
        e_field[2, x_idx, y_idx, z_idx, f_idx] = ez_list[:, f_idx]

    fields = xr.Dataset(
        {
            "E": (
                ("component", "x", "y", "z", "frequency"),
                e_field,
                {"Units": "V/m"},
            ),
        },
        coords={
            "component": ["x", "y", "z"],
            "x": x_sample_location_array,
            "y": y_sample_location_array,
            "z": z_sample_location_array,
            "frequency": sample_frequency_array,
        },
        attrs={
            "data_source_type": DataSourceType.HFSS,
            "field": FieldType.NEAR,
            "coordinate_system": CoordinateSystem.CARTESIAN,
        },
    )

    return fields