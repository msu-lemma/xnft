"""
Data writers for xarray formatted data.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from __future__ import annotations

from pathlib import Path

import xarray as xr


def write_dataset_hdf5(ds: xr.Dataset, file_path: Path):
    tmp_ds = ds.copy(deep=True)

    # Convert enums to save to file
    cs = tmp_ds.attrs["coordinate_system"].value
    tmp_ds.attrs["coordinate_system_name"] = cs.name
    tmp_ds.attrs["coordinate_components"] = cs.components
    del tmp_ds.attrs["coordinate_system"]

    coordinate_units_list = []
    for key, value in tmp_ds.attrs["coordinate_units"].items():
        coordinate_units_list.append(f"{key}, {value}")
    tmp_ds.attrs["coordinate_units"] = coordinate_units_list

    for da in tmp_ds.data_vars.values():
        if "units" in da.attrs:
            da.attrs["units"] = str(da.attrs["units"])

    tmp_ds.to_netcdf(file_path, engine="netcdf4", auto_complex=True)


def write_data_array_hdf5(da: xr.DataArray, file_path: Path, attrs=dict()):
    if isinstance(da, xr.DataArray):
        if "units" in da.attrs:
            da.attrs["units"] = str(da.attrs["units"])
        for key, value in attrs.items():
            da.attrs[key] = value

    da.to_netcdf(file_path, engine="netcdf4", auto_complex=True)
