"""
Field transform algorithms.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

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

from typing import Tuple
from numpy.typing import ArrayLike

from .enums import DataSourceType, FieldType, CoordinateSystemType
from .dtypes import FieldDataset

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
    # TODO: Update to type-2 NUFFT for improved performance (GPU won't be effective with type-3)

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

    return e_theta, e_phi


def planar_near_field_transform(
    near_field: xr.DataArray,
    probe_correction=None,
    frequencies=None,
    device="cpu",
    nthreads=0,
    return_xarray=True,
    n_phi=361,  # 0.5°/sample
    n_theta=361,  # 0.5°/sample
    window=windows.boxcar,
    r_far_field=1000,  # meters
) -> xr.Dataset | Tuple[ArrayLike]:
    # =========================================================================
    # Select Frequencies From Source File
    #
    #  TODO: Add multi-frequency processing
    #
    # The loaded source files above contain multiple frequency data.  Select a
    # single frequency to process.

    # List all frequencies available in file
    logger.debug(f"Available frequencies: {', '.join([
        str(Quantity(x, "Hz")) for x in near_field.frequency.values
    ])}")

    # Find nearest available frequency to the target frequency
    # target_frequency = frequencies[0]
    # if len(frequencies) > 1:
    #     logger.warning(
    #         f"Only single frequency planar near field "
    #         f"transforms are currently suppoerted.  Selecting "
    #         f"{str(Quantity(target_frequency, "Hz"))}"
    #     )

    # f_idx = np.argmin(np.abs(near_field.frequency.values - target_frequency))
    # frequency = near_field.frequency[f_idx]
    # wavelength = spc.c / frequency
    # k0 = 2.0 * np.pi / wavelength.item()

    # logger.debug(f"{' Selected Values ':{'-'}^{80}}")
    # logger.debug(f"Frequency: {Quantity(frequency, 'Hz')}")
    # logger.debug(f"Wavelength: {Quantity(wavelength, 'm')}")
    # logger.debug(f"k0: {Quantity(k0, 'rad/m')}")

    # =========================================================================
    # Compute uniform Theta, Phi grid for target NUDFT points

    theta_target = np.linspace(-np.pi / 2, np.pi / 2, n_theta)
    phi_target = np.linspace(-np.pi / 2, np.pi / 2, n_phi)

    theta_grid_target, phi_grid_target = np.meshgrid(theta_target, phi_target)

    # =========================================================================
    # Compute the near to far-field transform via non-uniform Fourier
    # transform (NUFFT)
    #
    # Select either CPU (via Numpy) or GPU (via CUDA).
    #
    # The following proceeds from [§12.9, 1].
    # [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
    #     N.J: Wiley-Interscience, 2005.
    win_x = window(near_field.x.size)
    win_y = window(near_field.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # === Perform FFTs =========================

    # fiNUFFT Reference: https://finufft.readthedocs.io/en/latest/math.html
    # Scale source sample locations along aperture to input of finufft \
    # [-pi/2, pi/2)

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

    # -- Generate field output --

    eta = (spc.mu_0 / spc.epsilon_0) ** 0.5
    h_theta = -e_phi / eta
    h_phi = e_theta / eta

    e_field = np.stack([e_phi, e_theta], axis=0)
    h_field = np.stack([h_phi, h_theta], axis=0)

    fields = FieldDataset.create(
        e_field=e_field,
        h_field=h_field,
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
