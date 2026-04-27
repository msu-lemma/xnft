"""
Field transform algorithms.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""
from __future__ import annotations

import numpy as np
import xarray as xr
import scipy.constants as spc
from scipy.signal import windows

import finufft

from quantiphy import Quantity

from joblib import Parallel, delayed

import logging
import warnings
import time

from typing import Callable, List

# from numpy.typing import ArrayLike

from ..enums import DataSourceType, FieldType, CoordinateSystemType
from ..dtypes import FieldDataset

# fmt: off
# MLX_AVAILABLE = False
# try:
#     import mlx.core as mx
#     MLX_AVAILABLE = True
# except ImportError:
#     MLX_AVAILABLE = False

# CUPY_AVAILABLE = False
# try:
#     import cupy as cp
#     CUPY_AVAILABLE = True
# except ImportError:
#     CUPY_AVAILABLE = False

# CUFINUFFT_AVAILABLE = False
# try:
#     import cufinufft
#     CUFINUFFT_AVAILABLE = True
# except ImportError:
#     CUFINUFFT_AVAILABLE = False
# fmt: on


logger = logging.getLogger(__name__)


def planar_near_field_transform_t3(
    theta_grid_target,
    phi_grid_target,
    k0,
    win,
    near_field_x_scaled,
    near_field_y_scaled,
    x_scale,
    y_scale,
    e_x,
    e_y,
    r_far_field=1000,
):
    # TODO: Add a type-2 NUFFT implementation for improved performance (GPU won't be effective with type-3)

    # Create target sample locations in k-space based on sample points in
    # (theta, phi)
    kx_target = k0 * np.sin(theta_grid_target) * np.cos(phi_grid_target)
    ky_target = k0 * np.sin(theta_grid_target) * np.sin(phi_grid_target)

    kx_target_scaled = (kx_target / x_scale).ravel()
    ky_target_scaled = (ky_target / y_scale).ravel()

    # Compute NUFFT
    precision = 1e-12
    nthreads = 0
    plan = finufft.Plan(
        nufft_type=3,
        n_modes_or_dim=2,
        eps=precision,
        nthreads=nthreads,
        dtype="complex128",
    )

    plan.setpts(
        x=near_field_x_scaled.astype(np.float64),
        y=near_field_y_scaled.astype(np.float64),
        s=kx_target_scaled.astype(np.float64),
        t=ky_target_scaled.astype(np.float64),
    )

    field_values_x = (win * e_x).ravel().astype(np.complex128)
    field_values_y = (win * e_y).ravel().astype(np.complex128)

    fe_x = plan.execute(field_values_x).reshape(theta_grid_target.shape)
    fe_y = plan.execute(field_values_y).reshape(phi_grid_target.shape)

    # Phase correction term such that phase at measured radius is constant
    greens_func = np.exp(-1j * k0 * r_far_field) / r_far_field
    c = k0 / (2.0 * np.pi)

    # fmt: off
    e_phi = (
        1j * c * greens_func * np.cos(theta_grid_target)
           * (-fe_x * np.sin(phi_grid_target) + fe_y * np.cos(phi_grid_target))
    )
    e_theta = (
        1j * c * greens_func * (fe_x * np.cos(phi_grid_target) + fe_y * np.sin(phi_grid_target))
    )
    # fmt: on

    return e_phi, e_theta


def planar_near_field_transform(
    near_field: xr.DataArray,
    frequencies: List[float],
    probe_correction: None | xr.DataArray = None,
    n_phi: int = 361,  # 0.5°/sample
    n_theta: int = 361,  # 0.5°/sample
    window: Callable = windows.boxcar,
    r_far_field=1000,  # meters
) -> xr.Dataset:
    """Compute the near to far-field transform via non-uniform fast Fourier transform (NUFFT).

    The NUFFT performed here uses the fiNUFFT package [1], [2], [3]. The plnar near-to-far field transform
    implementation proceeds from [§12.9, 4] and the derivation included in the documentation [citation needed].

    Parameters
    ----------
    near_field : xr.DataArray
        Planar near-field measured values to transform to far-field.
    frequencies : List[float]
        Frequencies in Hertz to perform the near-to-far field transform at.  If the provided frequency is not
        found in the `near_field` input, the nearest frequency present will be used instead and a warning will
        be raised to the user.
    probe_correction : None or xr.DataArray, optional
        Probe correction fields to use, if any. Must be far-field representations, by default None
    n_phi : int, optional
        Number of uniform phi sample points in the returned far-field, by default 361
    n_theta : int, optional
        Number of uniform theta sample points in the returned far-field, by default 361
    window : Callable, optional
        Window generating function used to spatially weight input sample points before transforming, by default
        scipy.signal.windows.boxcar.  Further windows can be found in the scipy.signal.windows module.
    r_far_field : int, optional
        Distance in meters to return the far field values at, by default 1000. This value is arbitrary, but may
        be helpful for comparing phase values derived from various sources.

    Returns
    -------
    xr.Dataset
        Far-field transformed fields stored in an xarray DataSet.

    References
    ----------
    [1] fiNUFFT Mathematical definitions of transforms. Online: https://finufft.readthedocs.io/en/latest/math.html
    [2] A. H. Barnett, J. F. Magland, and L. af Klinteberg, A parallel non-uniform fast Fourier transform library
        based on an “exponential of semicircle” kernel. SIAM J. Sci. Comput. 41(5), C479-C504 (2019).
        Online: https://arxiv.org/abs/1808.06736
    [3] A. H. Barnett, Aliasing error of the exp(𝛽√1-z2) kernel in the nonuniform fast Fourier transform.  Appl.
        Comput. Harmon. Anal. 51, 1-16 (2021). Online: https://arxiv.org/abs/2001.09405
    [4] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken, N.J: Wiley-Interscience, 2005.
    """

    # [Debug] List all frequencies available in file
    logger.debug(f"Available frequencies: {', '.join([
        str(Quantity(x, "Hz")) for x in near_field.frequency.values
    ])}")

    # Compute uniform Theta, Phi grid for target field points
    theta_target = np.linspace(-np.pi / 2, np.pi / 2, n_theta)
    phi_target = np.linspace(-np.pi / 2, np.pi / 2, n_phi)

    theta_grid_target, phi_grid_target = np.meshgrid(theta_target, phi_target)

    # Generate windowing function (rectangular by default)
    win_x = window(near_field.x.size)
    win_y = window(near_field.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # Scale source sample locations along aperture to input of finufft in the range [-pi/2, pi/2)
    x_scale = 2.0 * np.pi / (np.max(near_field.x.values) - np.min(near_field.x.values))
    y_scale = 2.0 * np.pi / (np.max(near_field.y.values) - np.min(near_field.y.values))

    near_field_yy, near_field_xx = np.meshgrid(near_field.y.values, near_field.x.values)

    near_field_x_scaled = (x_scale * near_field_xx).ravel()
    near_field_y_scaled = (y_scale * near_field_yy).ravel()

    # Start performance timer
    t_start = time.perf_counter()

    # Generate parallel function call arguments
    args_list = []
    z_val = near_field.coords["z"].item()  # should only have one z-height value

    for freq in frequencies:

        f_idx = np.argmin(np.abs(near_field.frequency.values - freq))
        nearest_freq = near_field.frequency.values[f_idx]

        if nearest_freq != freq:

            warnings.warn(
                "Provided frequency {:} not in available frequencies, using nearest frequency {:} instead".format(
                    Quantity(freq, "Hz"), Quantity(nearest_freq, "Hz")
                )
            )
            freq = nearest_freq

        wavelength = spc.c / freq
        k0 = 2.0 * np.pi / wavelength

        # Load E-field data from dataset
        # Dimensions (x, y, z, freq)
        e_x = near_field.sel(component="x", frequency=freq, z=z_val).values
        e_y = near_field.sel(component="y", frequency=freq, z=z_val).values

        args_list.append(
            dict(
                theta_grid_target=theta_grid_target,
                phi_grid_target=phi_grid_target,
                k0=k0,
                win=win,
                near_field_x_scaled=near_field_x_scaled,
                near_field_y_scaled=near_field_y_scaled,
                x_scale=x_scale,
                y_scale=y_scale,
                e_x=e_x,
                e_y=e_y,
                r_far_field=r_far_field,
            )
        )

    # Call planar near-field transform in parallel
    results = Parallel(n_jobs=-1)(
        delayed(planar_near_field_transform_t3)(**args) for args in args_list
    )

    e_phi_list, e_theta_list = zip(*results)

    # Stack along frequency axis
    # Result shape: (n_phi, n_theta, n_freq)
    e_phi = np.stack(e_phi_list, axis=-1)
    e_theta = np.stack(e_theta_list, axis=-1)

    # Print ellapsed time
    elapsed_time = Quantity(time.perf_counter() - t_start, "s")
    logger.debug("Far-field transform: {:}".format(elapsed_time))

    # Generate field output
    e_field = np.stack([e_phi, e_theta], axis=0)

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "phi": phi_target,
            "theta": theta_target,
        },
        frequency=frequencies,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=DataSourceType.HFSS,
    )
    return fields
