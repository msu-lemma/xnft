"""
Core logic for xnft.

Copyright 2025-2026 Michigan State University.
"""

import logging
import time

import numpy as np
import xarray as xr
import scipy.constants as spc
from scipy import signal
from scipy.signal import windows
from scipy import interpolate

MLX_AVAILABLE = False
try:
    MLX_AVAILABLE = True
    import mlx.core as mx
except ImportError:
    pass

from quantiphy import Quantity

from ..core.types import DataSourceType, FieldType, CoordinateSystem


logger = logging.getLogger(__name__)


def gen_near_field_sampling_grid():
    pass


def planar_near_field_transform(
    near_field_data,
    far_field_data,
    xfft_size=int(2**10),
    yfft_size=int(2**10),
    probe_correction=None,
    frequencies=None,
    device='gpu'
):
    # =========================================================================
    # ### Select Frequency From Source File
    # The loaded source files above contain multiple frequency data.  Select a
    # single frequency to process.

    # List all frequencies available in file
    frequency_list = [
        str(Quantity(x, "Hz")) for x in near_field_data.frequency.values
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

    f_idx = np.argmin(
        np.abs(near_field_data.frequency.values - target_frequency)
    )
    frequency = near_field_data.frequency[f_idx]
    wavelength = spc.c / frequency
    k0 = 2.0 * np.pi / wavelength.item()

    print(f"{' Selected Values ':{'-'}^{80}}")
    print(f"Frequency: {Quantity(frequency, 'Hz')}")
    print(f"Wavelength: {Quantity(wavelength, 'm')}")
    print(f"k0: {Quantity(k0, 'rad/m')}")

    # =========================================================================
    # ## Create the Spatial Sampling Grid

    x_length = (
        near_field_data.x.max() - near_field_data.x.min()
    ).values.item()
    y_length = (
        near_field_data.y.max() - near_field_data.y.min()
    ).values.item()

    print(f"x = {Quantity(x_length, 'm')}")
    print(f"y = {Quantity(y_length, 'm')}")

    dx = (near_field_data.x[1] - near_field_data.x[0]).values.item()
    dy = (near_field_data.y[1] - near_field_data.y[0]).values.item()

    print(f"dx = {Quantity(dx, 'm')}")
    print(f"dy = {Quantity(dy, 'm')}")

    xx, yy = np.meshgrid(near_field_data.x, near_field_data.y)

    # z_height = near_field_data.z.values[0]

    # =========================================================================
    # # Compute the $k$-space Sampling Grid
    # Compute maximum unambiguous viewing angle for φ=0° and φ=90° based on
    # sample spacing
    # TODO: Check for FOV based on height of measurement
    Nx = near_field_data.x.size
    Ny = near_field_data.y.size

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

    # win_x = windows.hamming(near_field_data.x.size)
    # win_y = windows.hamming(near_field_data.y.size)
    win_x = windows.boxcar(near_field_data.x.size)
    win_y = windows.boxcar(near_field_data.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # === Perform IFFTs =========================

    # Load E-field data
    e_x = near_field_data["E"].sel(component="x")[:, :, 0, f_idx].values
    e_y = near_field_data["E"].sel(component="y")[:, :, 0, f_idx].values

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
            near_field_data["E"].sel(component="x")[:, :, 0, f_idx].values
        )
        e_y = mx.array(
            near_field_data["E"].sel(component="y")[:, :, 0, f_idx].values
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
            "coordinate_system": CoordinateSystem.SPHERICAL,
        },
    )

    return fields

