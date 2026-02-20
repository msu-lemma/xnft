"""
Field transform algorithms.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
import time

import numpy as np
import xarray as xr
import scipy.constants as spc
from scipy.signal import windows

import finufft

from quantiphy import Quantity

from ..core.types import DataSourceType, FieldType, CoordinateSystemType

# fmt: off
MLX_AVAILABLE = False
try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

CUPY_AVAILABLE = False
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

CUFINUFFT_AVAILABLE = False
try:
    import cufinufft
    CUFINUFFT_AVAILABLE = True
except ImportError:
    CUFINUFFT_AVAILABLE = False
# fmt: on


logger = logging.getLogger(__name__)


def gen_near_field_sampling_grid():
    pass


def planar_near_field_transform(
    near_field,
    far_field,
    probe_correction=None,
    frequencies=None,
    device="gpu",
):
    # =========================================================================
    # Select Frequencies From Source File
    # TODO: Add multi-frequency processing
    # The loaded source files above contain multiple frequency data.  Select a
    # single frequency to process.

    # List all frequencies available in file
    frequency_list = [
        str(Quantity(x, "Hz")) for x in near_field.frequency.values
    ]
    print(f"Available frequencies: {', '.join(frequency_list)}")

    # Find nearest available frequency to the target frequency
    target_frequency = frequencies[0]
    if len(frequencies) > 1:
        logger.warning(
            f"Only single frequency planar near field "
            f"transforms are currently suppoerted.  Selecting "
            f"{str(Quantity(target_frequency, "Hz"))}"
        )

    f_idx = np.argmin(np.abs(near_field.frequency.values - target_frequency))
    frequency = near_field.frequency[f_idx]
    wavelength = spc.c / frequency
    k0 = 2.0 * np.pi / wavelength.item()

    print(f"{' Selected Values ':{'-'}^{80}}")
    print(f"Frequency: {Quantity(frequency, 'Hz')}")
    print(f"Wavelength: {Quantity(wavelength, 'm')}")
    print(f"k0: {Quantity(k0, 'rad/m')}")

    print(f"{near_field}")

    # =========================================================================
    # Create the near field spatial Sampling Grid

    x_length = (near_field.x.max() - near_field.x.min()).values.item()
    y_length = (near_field.y.max() - near_field.y.min()).values.item()

    print(f"x = {Quantity(x_length, 'm')}")
    print(f"y = {Quantity(y_length, 'm')}")

    dx = (near_field.x[1] - near_field.x[0]).values.item()
    dy = (near_field.y[1] - near_field.y[0]).values.item()

    print(f"dx = {Quantity(dx, 'm')}")
    print(f"dy = {Quantity(dy, 'm')}")

    # =========================================================================
    # Compute uniform Theta, Phi grid for target NUDFT points

    n_theta = 361
    n_phi = 361

    theta_range = [-np.pi / 2, np.pi / 2]
    phi_range = [0, np.pi]

    theta_target = np.linspace(*theta_range, n_theta)
    phi_target = np.linspace(*phi_range, n_phi)

    theta_grid_target, phi_grid_target = np.meshgrid(theta_target, phi_target)

    # =========================================================================
    # ## Compute the near to far-field transform
    # Select either CPU (via Numpy) or GPU (via CUDA).
    #
    # The following proceeds from [§12.9, 1].
    # [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
    #     N.J: Wiley-Interscience, 2005.

    # win_x = windows.hamming(near_field.x.size)
    # win_y = windows.hamming(near_field.y.size)
    win_x = windows.boxcar(near_field.x.size)
    win_y = windows.boxcar(near_field.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # === Perform FFTs =========================

    # Load E-field data
    e_x = near_field["E"].sel(component="x")[:, :, 0, f_idx].values
    e_y = near_field["E"].sel(component="y")[:, :, 0, f_idx].values

    # Select device for FFT
    device = "cpu"  # 'cpu' or 'gpu'

    # Start performance timer
    t_start = time.perf_counter()

    # Perform setup for CPU and GPU
    if device == "gpu" and CUFINUFFT_AVAILABLE:
        device = "gpu"
        # --- CUDA GPU Implementation ---------------
        # Set namespace to cupy
        ns = cp
        nufft = cufinufft
    else:
        # --- Numpy CPU Implementation -------------
        # Set namespace to numpy
        device = "cpu"
        ns = np
        nufft = finufft

    print(f"Device: {device.upper()}")

    # fiNUFFT Reference: https://finufft.readthedocs.io/en/latest/math.html
    # Scale source sample locations along aperture to input of finufft \
    # [-pi/2, pi/2)

    # eps = 1e-12  # small epsilon to avoid aliasing at pi
    x_scale = (
        2.0
        * ns.pi
        / (ns.max(near_field.x.values) - ns.min(near_field.x.values))
    )
    y_scale = (
        2.0
        * ns.pi
        / (ns.max(near_field.y.values) - ns.min(near_field.y.values))
    )

    near_field_yy, near_field_xx = ns.meshgrid(
        near_field.y.values, near_field.x.values
    )

    near_field_x_scaled = (x_scale * near_field_xx).ravel()
    near_field_y_scaled = (y_scale * near_field_yy).ravel()

    print(
        f"near_field_x_scaled:\t\t[{np.min(near_field_x_scaled) / np.pi}, \
            {np.max(near_field_x_scaled) / np.pi}] π"
    )
    print(
        f"near_field_x_scaled:\t\t[{np.min(near_field_x_scaled) / np.pi}, \
            {np.max(near_field_x_scaled) / np.pi}] π"
    )

    # Create target sample locations in k-space based on sample points in
    # (theta, phi)
    kx_target = k0 * ns.sin(theta_grid_target) * ns.cos(phi_grid_target)
    ky_target = k0 * ns.sin(theta_grid_target) * ns.sin(phi_grid_target)

    kx_target_scaled = (kx_target / x_scale).ravel()
    ky_target_scaled = (ky_target / y_scale).ravel()

    # Compute NUFFT
    nthreads = 0  # 0 uses maximum available
    precision = 1e-12

    plan = nufft.Plan(
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
    r_ff = 100  # TODO: compute based on aperture size
    greens_func = ns.exp(-1j * k0 * r_ff) / r_ff
    c = k0 / (2.0 * np.pi)

    e_phi = (
        1j
        * c
        * greens_func
        * ns.cos(theta_grid_target)
        * (-fe_x * ns.sin(phi_grid_target) + fe_y * ns.cos(phi_grid_target))
    )
    e_theta = (
        1j
        * c
        * greens_func
        * (fe_x * ns.cos(phi_grid_target) + fe_y * ns.sin(phi_grid_target))
    )

    # Compute magnitude of E-field to plot
    e_total = ns.sqrt(e_phi**2 + e_theta**2)

    # If using GPU memory, create view of memory for numpy
    if device == "gpu":
        e_total = np.array(e_total, copy=False)
        theta_grid_target = np.array(theta_grid_target, copy=False)
        phi_grid_target = np.array(phi_grid_target, copy=False)
        e_phi = np.array(e_phi, copy=False)
        e_theta = np.array(e_theta, copy=False)
        fe_x = np.array(fe_x, copy=False)
        fe_y = np.array(fe_y, copy=False)

    t_end = time.perf_counter()
    elapsed_time = Quantity(t_end - t_start, "s")
    print("Far-field transform:", elapsed_time)

    # -- Generate field output --

    eta = (spc.mu_0 / spc.epsilon_0) ** 0.5
    h_theta = -e_phi / eta
    h_phi = e_theta / eta

    e_field = np.stack([e_phi, e_theta])[..., np.newaxis]
    h_field = np.stack([h_phi, h_theta])[..., np.newaxis]

    fields = xr.Dataset(
        {
            "E": (
                ("component", "phi", "theta", "frequency"),
                e_field,
                {"Units": "V/m"},
            ),
            "H": (
                ("component", "phi", "theta", "frequency"),
                h_field,
                {"Units": "A/m"},
            ),
        },
        coords={
            "component": ["phi", "theta"],
            "phi": phi_target,
            "theta": theta_target,
            "frequency": [frequency],
        },
        attrs={
            "data_source_type": DataSourceType.XNFT,
            "field": FieldType.FAR,
            "coordinate_system": CoordinateSystemType.SPHERICAL,
        },
    )

    return fields


def planar_near_field_transform_fft(
    near_field,
    far_field_data,
    xfft_size=int(2**10),
    yfft_size=int(2**10),
    probe_correction=None,
    frequencies=None,
    device="gpu",
):
    # =========================================================================
    # ### Select Frequency From Source File
    # The loaded source files above contain multiple frequency data.  Select a
    # single frequency to process.

    # List all frequencies available in file
    frequency_list = [
        str(Quantity(x, "Hz")) for x in near_field.frequency.values
    ]
    print(f"Available frequencies: {', '.join(frequency_list)}")

    # Find nearest available frequency to the target frequency
    target_frequency = frequencies[0]
    if len(frequencies) > 1:
        logger.warning(
            f"Only single frequency planar near field "
            f"transforms are currently suppoerted.  Selecting "
            f"{str(Quantity(target_frequency, "Hz"))}"
        )

    f_idx = np.argmin(np.abs(near_field.frequency.values - target_frequency))
    frequency = near_field.frequency[f_idx]
    wavelength = spc.c / frequency
    k0 = 2.0 * np.pi / wavelength.item()

    print(f"{' Selected Values ':{'-'}^{80}}")
    print(f"Frequency: {Quantity(frequency, 'Hz')}")
    print(f"Wavelength: {Quantity(wavelength, 'm')}")
    print(f"k0: {Quantity(k0, 'rad/m')}")

    # =========================================================================
    # ## Create the Spatial Sampling Grid

    x_length = (near_field.x.max() - near_field.x.min()).values.item()
    y_length = (near_field.y.max() - near_field.y.min()).values.item()

    print(f"x = {Quantity(x_length, 'm')}")
    print(f"y = {Quantity(y_length, 'm')}")

    dx = (near_field.x[1] - near_field.x[0]).values.item()
    dy = (near_field.y[1] - near_field.y[0]).values.item()

    print(f"dx = {Quantity(dx, 'm')}")
    print(f"dy = {Quantity(dy, 'm')}")

    xx, yy = np.meshgrid(near_field.x, near_field.y)

    # z_height = near_field.z.values[0]

    # =========================================================================
    # # Compute the $k$-space Sampling Grid
    # Compute maximum unambiguous viewing angle for φ=0° and φ=90° based on
    # sample spacing
    # TODO: Check for FOV based on height of measurement
    Nx = near_field.x.size
    Ny = near_field.y.size

    # NOTE: _All_ following code assumes sampling gird is centered around (0,0)
    # on the aperture (center of aperture).
    # Compute the k-space sampling grid

    interpolated_x_size = xfft_size - 1
    interpolated_y_size = yfft_size - 1

    kx = (
        np.linspace(-Nx / 2, Nx / 2, interpolated_x_size, endpoint=True)
        * 2.0
        * np.pi
        / x_length
    )
    ky = (
        np.linspace(-Ny / 2, Ny / 2, interpolated_y_size, endpoint=True)
        * 2.0
        * np.pi
        / y_length
    )

    kz = np.emath.sqrt(k0**2 - kx**2 - ky**2).real

    print(f"max(kx) = {kx.max().item()} rad/m")
    print(f"max(ky) = {ky.max().item()} rad/m")
    print(f"max(kz) = {kz.max().item()} rad/m")

    dkx = kx[1] - kx[0]
    dky = ky[1] - ky[0]

    print(f"dkx = {dkx.item()} rad/m")
    print(f"dky = {dky.item()} rad/m")

    kxx, kyy = np.meshgrid(kx, ky)
    kzz = np.emath.sqrt(k0**2 - kxx**2 - kyy**2)

    # =========================================================================

    # ## Project sampling grid onto spherical wavefront angles (polar
    # coordinates)

    phi = np.atan2(kyy, kxx).real[:, 0]
    theta = np.arccos(kz / k0).real * np.sign(phi)

    phi_grid = np.atan2(kyy, kxx).real
    theta_grid = np.arccos(kzz / k0).real

    # =========================================================================
    # ## Compute the near to far-field transform
    # Select either CPU (via Numpy) or GPU (via MLX).  MLX supports Metal GPUs
    # (Apple M-series processors) or Nvidia GPUs (Linux only).
    #
    # The following proceeds from [§12.9, 1].
    # [1] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken,
    #     N.J: Wiley-Interscience, 2005.

    # win_x = windows.hamming(near_field.x.size)
    # win_y = windows.hamming(near_field.y.size)
    win_x = windows.boxcar(near_field.x.size)
    win_y = windows.boxcar(near_field.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # === Perform IFFTs =========================

    # Load E-field data
    e_x = near_field["E"].sel(component="x")[:, :, 0, f_idx].values
    e_y = near_field["E"].sel(component="y")[:, :, 0, f_idx].values

    # Select device for FFT
    print(f"Device: {device.upper()}")

    # Start performance timer
    t_start = time.perf_counter()

    # Perform setup for CPU and GPU
    if device == "gpu" and MLX_AVAILABLE:
        # --- Metal GPU Implementation ---------------
        # NOTE: Metal only supports single precision complex floats
        # (i.e., complex64)

        # Set namespace to mlx
        ns = mx

        # --- Copy arrays into GPU memory ---
        # Delete main memory copy of sample grids to save space
        theta_grid = mx.array(theta_grid)
        phi_grid = mx.array(phi_grid)

        win = mx.array(win)
        e_x = mx.array(
            near_field["E"].sel(component="x")[:, :, 0, f_idx].values
        )
        e_y = mx.array(
            near_field["E"].sel(component="y")[:, :, 0, f_idx].values
        )
    else:
        # --- Numpy CPU Implementation -------------
        # Set namespace to numpy
        ns = np

    # --- Compute the FFT ---
    fe_x = ns.fft.ifftshift(
        ns.fft.ifftn(
            a=win * e_x,
            s=(interpolated_x_size, interpolated_y_size),
            axes=(1, 0),
        ),
        axes=(1, 0),
    )  # (12-85a)
    fe_y = ns.fft.ifftshift(
        ns.fft.ifftn(
            a=win * e_y,
            s=(interpolated_x_size, interpolated_y_size),
            axes=(1, 0),
        ),
        axes=(1, 0),
    )  # (12-85b)
    # fe_z = -(fe_x * kxx + fe_y * kyy) / kzz  # (12-84b)

    # Phase correction term such that phase at measured radius is constant
    r_ff = 10  # TODO: compute based on aperture size
    greens_func = ns.exp(-1j * k0 * r_ff) / r_ff

    c = k0 / (2.0 * np.pi)

    e_phi = (
        1j
        * c
        * greens_func
        * ns.cos(theta_grid)
        * (-fe_x * ns.sin(phi_grid) + fe_y * ns.cos(phi_grid))
    )
    e_theta = (
        1j
        * c
        * greens_func
        * (fe_x * ns.cos(phi_grid) + fe_y * ns.sin(phi_grid))
    )

    e_phi = np.where(theta_grid <= 0, np.nan, e_phi)
    e_theta = np.where(theta_grid <= 0, np.nan, e_theta)

    # Compute magnitude of E-field to plot
    e_total = ns.sqrt(e_phi**2 + e_theta**2)

    # If using GPU memory, create view of memory for numpy
    if device == "gpu":
        e_total = np.array(e_total, copy=False)
        theta_grid = np.array(theta_grid, copy=False)
        phi_grid = np.array(phi_grid, copy=False)
        e_phi = np.array(e_phi, copy=False)
        e_theta = np.array(e_theta, copy=False)
        fe_x = np.array(fe_x, copy=False)
        fe_y = np.array(fe_y, copy=False)

    t_end = time.perf_counter()
    elapsed_time = Quantity(t_end - t_start, "s")
    print("Far-field transform:", elapsed_time)

    # -- Generate field output --

    eta = (spc.mu_0 / spc.epsilon_0) ** 0.5
    h_theta = -e_phi / eta
    h_phi = e_theta / eta

    e_field = np.stack([e_phi, e_theta])[..., np.newaxis]
    h_field = np.stack([h_phi, h_theta])[..., np.newaxis]

    fields = xr.Dataset(
        {
            "E": (
                ("component", "phi", "theta", "frequency"),
                e_field,
                {"Units": "V/m"},
            ),
            "H": (
                ("component", "phi", "theta", "frequency"),
                h_field,
                {"Units": "A/m"},
            ),
        },
        coords={
            "component": ["phi", "theta"],
            "phi": phi,
            "theta": theta,
            "frequency": [frequency],
        },
        attrs={
            "data_source_type": DataSourceType.XNFT,
            "field": FieldType.FAR,
            "coordinate_system": CoordinateSystemType.SPHERICAL,
        },
    )

    return fields
