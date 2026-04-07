"""
Module providing data types specific to xnft.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import numpy as np
from numpy.typing import ArrayLike
import xarray as xr

from typing import Dict, Optional
import unyt

from .enums import FieldType, CoordinateSystemType, DataSourceType

import xarray as xr
import unyt


# Allowed coordinate system types for near/far-field

NEAR_FIELD_CS_TYPES = {
    CoordinateSystemType.CARTESIAN: {"x": unyt.meter, "y": unyt.meter, "z": unyt.meter},
    CoordinateSystemType.CYLINDRICAL: {"rho": unyt.meter, "phi": unyt.radian, "z": unyt.meter},
    CoordinateSystemType.SPHERICAL: {"r": unyt.meter, "phi": unyt.radian, "theta": unyt.radian},
}

FAR_FIELD_CS_TYPES = {
    CoordinateSystemType.SPHERICAL: {"phi": unyt.radian, "theta": unyt.radian},
}

class FieldDataset:
    """
    Simple helper constructor to store fields as xarray datasets.
    """

    @staticmethod
    def create(
        *,
        e_field: ArrayLike,
        h_field: Optional[ArrayLike | None] = None,
        spatial_coords: Dict[ArrayLike],
        frequency: ArrayLike,
        coordinate_system: CoordinateSystemType,
        field_type: FieldType,
        data_source: DataSourceType,
    ) -> xr.Dataset:
        """Create xarray field dataset with data validation.

        Parameters
        ----------
        e_field : ArrayLike
            3D Electric field tensor, shape (3, nx, ny, nz)
        h_field : ArrayLike
            3D Magnetic field tensor, shape (3, nx, ny, nz)
        spatial_coords : Dict[ArrayLike]
            Mapping from component name to coordinate vector
        frequency : ArrayLike
            Vector of frequencies contained in field tensor
        coordinate_system : CoordinateSystemType
            Coordinate system used for data
        field_type : FieldType
            Type of field: Near-Field / Far-Field
        data_source : DataSourceType
            Source of data, e.g., ANSYS HFSS, LEmmA scanner, etc.

        Returns
        -------
        xr.Dataset
            Field dataset with validated components and attributes
        """

        components = coordinate_system.value.components

        # Ignore first dimension (radial) if in far-field
        if field_type is FieldType.FAR:
            components = components[1:]
        
        spatial_dims = components
        dims = ("component", *spatial_dims, "frequency")
        print(dims)

        # --- Validate Inputs ---

        if field_type is FieldType.FAR and coordinate_system not in FAR_FIELD_CS_TYPES:
            raise ValueError("Far-field must use spherical coordinates")

        if field_type is FieldType.NEAR and coordinate_system not in NEAR_FIELD_CS_TYPES:
            raise ValueError(f"Invalid coordinate system for near-field. Must be one of {','.join([x.name for x in NEAR_FIELD_CS_TYPES])}")

        expected_ndim = len(dims)
        if e_field.ndim != expected_ndim:
            raise ValueError(
                f"Field ndim={e_field.ndim}, expected {expected_ndim}"
            )
        
        for dim in spatial_dims:
            if dim not in spatial_coords:
                raise ValueError(f"Missing coordinate '{dim}' in spatial_coords")
        
        if h_field is not None:
            if e_field.shape != h_field.shape:
                raise ValueError("E- and H-field shapes must match, otherwise H-field must be None")


        # --- Create Dataset ---
        coords = {
            "component": list(components),
            **spatial_coords,
            "frequency": frequency,
        }
        
        if field_type is FieldType.NEAR:
            coordinate_units = NEAR_FIELD_CS_TYPES[coordinate_system]
        else:
            coordinate_units = FAR_FIELD_CS_TYPES[coordinate_system]

        # Add frequency units
        coordinate_units['frequency'] = unyt.hertz

        data_vars = {
            "E": (
                    dims,
                    e_field,
                    {"units": unyt.volt / unyt.meter},
                )
        }

        if h_field is not None:
            data_vars["H"] = (
                dims,
                h_field,
                {"units": unyt.ampere / unyt.meter},
            )

        return xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs={
                "data_source_type": data_source,
                "field_type": field_type,
                "coordinate_system": coordinate_system,
                "coordinate_units": coordinate_units
            },
        )
