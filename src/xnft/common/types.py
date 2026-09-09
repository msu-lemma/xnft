"""
Module providing data types specific to xnft.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import unyt
import xarray as xr
from numpy.typing import NDArray

from xnft.common.enums import PolarizationType, SParameterType

from ..calibration.gain import GainCalibration
from .enums import CoordinateSystemType, DataSourceType, FieldType

# Allowed coordinate system types for near/far-field

NEAR_FIELD_CS_TYPES = {
    CoordinateSystemType.CARTESIAN: {"x": unyt.meter, "y": unyt.meter, "z": unyt.meter},
    CoordinateSystemType.CYLINDRICAL: {
        "rho": unyt.meter,
        "phi": unyt.radian,
        "z": unyt.meter,
    },
    CoordinateSystemType.SPHERICAL: {
        "r": unyt.meter,
        "phi": unyt.radian,
        "theta": unyt.radian,
    },
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
        e_field: NDArray,
        h_field: NDArray | None = None,
        spatial_coords: dict[str, NDArray],
        frequency: NDArray,
        coordinate_system: CoordinateSystemType,
        field_type: FieldType,
        data_source: DataSourceType,
        aperture_size: float = 0.0,
        gain_calibration: GainCalibration | None = None,
    ) -> xr.Dataset:
        """Create xarray field dataset with data validation.

        Parameters
        ----------
        e_field : NDArray
            3D Electric field tensor, shape (3, nx, ny, nz)
        h_field : NDArray
            3D Magnetic field tensor, shape (3, nx, ny, nz)
        spatial_coords : Dict[NDArray]
            Mapping from component name to coordinate vector
        frequency : NDArray
            Vector of frequencies contained in field tensor
        coordinate_system : CoordinateSystemType
            Coordinate system used for data
        field_type : FieldType
            Type of field: Near-Field / Far-Field
        data_source : DataSourceType
            Source of data, e.g., ANSYS HFSS, LEmmA scanner, etc.
        aperture_size : float, optional
            Largest dimension of the aperture inducing the field in meters
            Used to compute valid observation angles, by default 0.0
        gain_calibration : GainCalibration, optional
            Gain calibration object containing standard and measurement
            fields used to create a gain correction lookup table. By default None

        Returns
        -------
        xr.Dataset
            Field dataset with validated components and attributes
        """

        components = coordinate_system.value.components

        frequency = np.atleast_1d(frequency)

        if e_field.shape[-1] != len(frequency):
            raise ValueError(
                f"Mismatch: e_field.shape[-1]={e_field.shape[-1]} "
                f"but len(frequency)={len(frequency)}"
            )

        # Ignore first dimension (radial) if in far-field
        if field_type is FieldType.FAR:
            components = components[1:]

        spatial_dims = components
        dims = ("component", *spatial_dims, "frequency")

        # --- Validate Inputs ---

        if field_type is FieldType.FAR and coordinate_system not in FAR_FIELD_CS_TYPES:
            raise ValueError("Far-field must use spherical coordinates")

        if (
            field_type is FieldType.NEAR
            and coordinate_system not in NEAR_FIELD_CS_TYPES
        ):
            raise ValueError(
                f"Invalid coordinate system for near-field. Must be one of {','.join([x.name for x in NEAR_FIELD_CS_TYPES])}"
            )

        expected_ndim = len(dims)
        if e_field.ndim != expected_ndim:
            raise ValueError(f"Field ndim={e_field.ndim}, expected {expected_ndim}")

        for dim in spatial_dims:
            if dim not in spatial_coords:
                raise ValueError(f"Missing coordinate '{dim}' in spatial_coords")

        if h_field is not None and e_field.shape != h_field.shape:
            raise ValueError(
                "E- and H-field shapes must match, otherwise H-field must be None"
            )

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
        coordinate_units["frequency"] = unyt.hertz

        data_vars = {
            "E": (
                dims,
                e_field,
                {"units": f"{unyt.volt}/{unyt.meter}"},
            )
        }

        if h_field is not None:
            data_vars["H"] = (
                dims,
                h_field,
                {"units": f"{unyt.ampere}/{unyt.meter}"},
            )

        return xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs={
                "data_source_type": data_source,
                "field_type": field_type,
                "coordinate_system": coordinate_system,
                "coordinate_units": coordinate_units,
                "aperture_size": aperture_size,
                "gain_calibration": gain_calibration,
            },
        )


@dataclass
class FileInfo:
    """
    File path and metatdata struct.

    Parameters
    ----------
    path : pathlib.Path
        Path to file.
    polarization : PolarizationTye or Set[PolarizationType], optional
        Polarization of data stored in file, may be a typle of both co-
        and cross-pol, by default {PolarizationType.CO_POL, PolarizationType.CROSS_POL}
    s_parameters : Set[SParameterType]
        S-Parameter in file to load for processing
    """

    path: Path
    polarization: PolarizationType | set[PolarizationType] = field(
        default_factory=lambda: {
            PolarizationType.CO_POL,
            PolarizationType.CROSS_POL,
        }
    )
    s_parameters: set[SParameterType] = field(default_factory=set)
