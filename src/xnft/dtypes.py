"""Module providing classes specific to xnft."""

import numpy as np
import xarray as xr


class FieldData:
    """
    Class for storing and manipulating field data.
    """

    def __init__(self):
        # Create default near-field measured data object
        self.near_field = xr.DataArray(
            data=np.empty((0, 0, 0, 0), dtype=np.complex128),
            dims=["x", "y", "z", "frequency"],
            attrs={
                "description": "Near-field measurement data.",
                "units": "",
                "type": "planar",
            },
            coords={
                "probe_location": (
                    ["x", "y", "z"],
                    np.empty((0, 0, 0), dtype=np.complex128),
                ),
                "frequency": np.empty((0,), dtype=np.complex128),
            },
        )

        # Create default far-field measured data object
        self.far_field = xr.DataArray(
            data=np.empty((0, 0, 0), dtype=np.complex128),
            dims=["theta", "phi", "frequency"],
            attrs={"description": "Far-field measurement data.", "units": ""},
            coords={
                "field_location": (
                    ["theta", "phi"],
                    np.empty((0, 0), dtype=np.complex128),
                ),
                "frequency": np.empty((0,), dtype=np.complex128),
            },
        )
