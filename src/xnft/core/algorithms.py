"""
Core logic for xnft.

Copyright 2025-2026 Michigan State University.
"""

import logging
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.constants as spc
from scipy import signal
from scipy.signal import windows
from scipy import interpolate

from matplotlib.ticker import EngFormatter

import numpy.fft as npfft

# TODO: Add logic to detect if MLX is installed
import mlx.core as mx
import mlx.core.fft as mxfft

from quantiphy import Quantity

# Create unit formatters
fmt_hz = EngFormatter(unit="Hz")
fmt_s = EngFormatter(unit="s")
fmt_m = EngFormatter(unit="m")
fmt_rps = EngFormatter(unit="rad/s")
fmt_rpm = EngFormatter(unit="rad/m")
fmt_rad = EngFormatter(unit="rad")
fmt_prad = EngFormatter(unit=r"$\pi$ rad")
fmt_deg = EngFormatter(unit=r"°")

logger = logging.getLogger(__name__)


# def coordinates()


def planar_near_field_transform(
    near_field_data,
    far_field_data,
    xfft_size=int(2**10),
    yfft_size=int(2**10),
    probe_correction=None,
    frequencies=None,
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
    print(f"Wavelength: {Quantity(wavelength,'m')}")
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

    interpolated_x_size = interpolated_y_size = 2**12 - 1

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

    phi_grid = np.atan2(kyy, kxx).real
    theta_grid = np.arccos(kzz / k0).real

    # =========================================================================
    # ## Compute the near to far-field transform
    # Select either CPU (via Numpy) or GPU (via MLX).  MLX supports Metal GPUs
    # (Apple M-series processors) or Nvidia GPUs.
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
    device = "cpu"  # 'cpu' or 'gpu'
    print(f"Device: {device.upper()}")

    # Start performance timer
    t_start = time.perf_counter()

    # Perform setup for CPU and GPU
    if device == "cpu":
        # --- Numpy CPU Implementation -------------
        # Set namespace to numpy
        ns = np

    elif device == "gpu":
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
        * np.cos(theta_grid)
        * (-fe_x * np.sin(phi_grid) + fe_y * np.cos(phi_grid))
    )
    e_theta = (
        1j
        * c
        * greens_func
        * (fe_x * np.cos(phi_grid) + fe_y * np.sin(phi_grid))
    )

    # Compute magnitude of E-field to plot
    e_total = np.sqrt(e_phi**2 + e_theta**2)

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


# ----------------------------------------------------------------------------


def planar_near_field_transform_full(
    near_field_data,
    far_field_data,
    xfft_size=int(2**10),
    yfft_size=int(2**10),
    probe_correction=None,
    frequencies=None,
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
    f_idx = np.argmin(
        np.abs(near_field_data.frequency.values - target_frequency)
    )
    frequency = near_field_data.frequency[f_idx]
    wavelength = spc.c / frequency
    k0 = 2.0 * np.pi / wavelength.item()

    print(f"{' Selected Values ':{'-'}^{80}}")
    print(f"Frequency: {Quantity(frequency, 'Hz')}")
    print(f"Wavelength: {Quantity(wavelength,'m')}")
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

    z_height = near_field_data.z.values[0]

    # =========================================================================
    # ## Plot Near-Field data
    # While not strictly necessary, it can be informative to view the
    # near-field.

    # Compute magnitude of near-field data
    e_mag_nf = np.linalg.norm(np.abs(near_field_data["E"]), ord=2, axis=0)

    fig, ax = plt.subplots(1, 1)

    # Set zero E-field values to very small value to render in dB nicely
    e_mag_nf_tmp = e_mag_nf
    e_mag_nf_tmp[e_mag_nf_tmp == 0] = 1e-12
    e_mag_nf_db = 20 * np.log10(e_mag_nf_tmp[:, :, 0, f_idx].T)

    vmax = e_mag_nf_db.max()
    vmin = vmax - 40

    c = ax.imshow(
        e_mag_nf_db,
        origin="lower",
        extent=(
            near_field_data.x.min(),
            near_field_data.x.max(),
            near_field_data.y.min(),
            near_field_data.y.max(),
        ),
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_aspect("equal")
    fig.colorbar(c, label=r"$|\mathbf{{E}}|$ (dBV/m)")

    ax.set_title(rf"Near-Field $|\mathbf{{E}}|$, z={Quantity(z_height, 'm')}")
    ax.set_xlabel("X Displacement")
    ax.set_ylabel("Y Displacement")

    ax.xaxis.set_major_formatter(fmt_m)
    ax.yaxis.set_major_formatter(fmt_m)

    ax.tick_params("x", rotation=-30)

    fig.tight_layout()
    plt.show()

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

    interpolated_x_size = interpolated_y_size = 2**12 - 1

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

    # Compute spherical wavefront angles
    phi = np.atan2(kyy, kxx).real[:, 0]
    theta = np.arccos(kz / k0).real * np.sign(phi)

    phi_grid = np.atan2(kyy, kxx).real
    theta_grid = np.arccos(kzz / k0).real

    if theta_grid.size < 2**26:

        show_grids = False
        if show_grids is True:
            # Plot the phi_grid and theta_grid variables
            fig, axs = plt.subplots(1, 2, sharex=True, sharey=True)
            axs[0].set_title("phi_grid")
            axs[0].imshow(phi_grid)
            axs[1].set_title("theta_grid")
            axs[1].imshow(theta_grid)

            fig.tight_layout()

        # Plot the sampling grid
        fig, ax = plt.subplots(1, 1, subplot_kw={"projection": "polar"})

        theta_loc = theta_grid[theta_grid < np.pi / 2.0001].real
        phi_loc = phi_grid[theta_grid < np.pi / 2.0001]
        ax.scatter(phi_loc, theta_loc, marker=".", color="red", s=0.5)

        ax.set_rmin(0)
        ax.set_rmax(np.pi / 2)
        ax.set_rgrids(
            [0, np.pi / 4, np.pi / 2], labels=["0", "45°", r"$\theta=90°$"]
        )
        ax.set_thetagrids(
            [x * 45 for x in range(8)],
            labels=[
                r"  $\phi=0°$" if x == 0 else rf"{x*45}°" for x in range(8)
            ],
        )

        ax.set_title("$k$-space Sampling Grid")
        # ax.yaxis.set_major_formatter(lambda x,y: fr'{np.rad2deg(x):0.0f}°')

        fig.tight_layout()
    else:
        print("Too many points to plot. Skipping sampling grid...")

    # =========================================================================
    # ## Compute the near to far-field transform
    # Select either CPU (via Numpy) or GPU (via MLX).  MLX supports Metal GPUs
    # (Apple M-series processors) or Nvidia GPUs.
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
    device = "cpu"  # 'cpu' or 'gpu'
    print(f"Device: {device.upper()}")

    # Start performance timer
    t_start = time.perf_counter()

    # Perform setup for CPU and GPU
    if device == "cpu":
        # --- Numpy CPU Implementation -------------
        # Set namespace to numpy
        ns = np

    elif device == "gpu":
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
        * np.cos(theta_grid)
        * (-fe_x * np.sin(phi_grid) + fe_y * np.cos(phi_grid))
    )
    e_theta = (
        1j
        * c
        * greens_func
        * (fe_x * np.cos(phi_grid) + fe_y * np.sin(phi_grid))
    )

    # Compute magnitude of E-field to plot
    e_total = np.sqrt(e_phi**2 + e_theta**2)

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

    # =========================================================================

    # Interpolate data points to uniform sphere
    # TODO

    # =========================================================================
    # Plot the far-field patterns

    e_mag = np.abs(e_total)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), sharex=True, sharey=True)
    # fig = plt.figure()
    # axs = [None, None]
    # axs[0] = fig.add_subplot(2,1,1,projection='polar')
    # axs[1] = fig.add_subplot(2,1,2,projection='polar')

    print(
        f"Theta:\t\t[{np.min(theta_grid) / np.pi}, {np.max(theta_grid) / np.pi}] π"
    )
    print(
        f"Phi:\t\t[{np.min(phi_grid) / np.pi}, {np.max(phi_grid) / np.pi}] π"
    )

    # Convert polar to cartesian to plot on pcolormesh
    xloc = theta_grid * np.sin(phi_grid) * 180 / np.pi
    yloc = theta_grid * np.cos(phi_grid) * 180 / np.pi

    c = axs[0].pcolormesh(
        xloc,
        yloc,
        20 * np.log10(e_mag / np.max(e_mag)),
        shading="nearest",
        vmax=0,
        vmin=-60,
    )

    axs[0].set_aspect("equal")
    plt.colorbar(c, ax=axs[0], label=r"$|\mathbf{E}|$ (dB, Normalized)")

    axs[0].set_title(r"Polar $|\mathbf{E}|$ Projection (xNFT)")
    axs[0].set_ylabel(r"Elevation ($\theta$)")
    axs[0].set_xlabel(r"Elevation ($\theta$)")

    axs[0].xaxis.set_major_formatter(fmt_deg)
    axs[0].yaxis.set_major_formatter(fmt_deg)

    # --- Plot "benchmark" far-field data ---

    if far_field_data:
        e_mag_ff = np.linalg.norm(np.abs(far_field_data["E"]), ord=2, axis=0)

        print(
            f"FF Theta:\t[{np.min(far_field_data.theta.values) / np.pi}, "
            f"{np.max(far_field_data.theta.values) / np.pi}] π"
        )
        print(
            f"FF Phi:\t\t[{np.min(far_field_data.phi.values) / np.pi}, "
            f"{np.max(far_field_data.phi.values) / np.pi}] π"
        )

        ff_theta = far_field_data.theta
        ff_phi = far_field_data.phi

        ff_theta_grid, ff_phi_grid = np.meshgrid(ff_theta, ff_phi)
        xloc_ref = ff_theta_grid * np.cos(ff_phi_grid) * 180 / np.pi
        yloc_ref = ff_theta_grid * np.sin(ff_phi_grid) * 180 / np.pi

        emag = e_mag_ff[:, :, f_idx]

        c = axs[1].pcolormesh(
            xloc_ref,
            yloc_ref,
            20 * np.log10(emag / np.max(emag)),
            shading="nearest",
            vmax=0,
            vmin=-60,
        )

        # axs[1].pcolormesh(ff_theta_grid, ff_phi_grid, emag, shading="nearest")
        plt.colorbar(c, ax=axs[1], label=r"$|\mathbf{E}|$ (dB, Normalized)")

        axs[1].set_aspect("equal")

        axs[1].set_title(r"Polar $|\mathbf{E}|$ Projection (Reference)")
        axs[1].set_ylabel(r"Elevation ($\theta$)")
        axs[1].set_xlabel(r"Elevation ($\theta$)")

        axs[1].xaxis.set_major_formatter(fmt_deg)
        axs[1].yaxis.set_major_formatter(fmt_deg)

    fig.tight_layout()
    plt.show()

    # --- Plot 1D slices ---

    # fig, axs = plt.subplots(3,2, figsize=(12,6))
    fig, axs = plt.subplots(3, 1, figsize=(6, 6), squeeze=False)

    phi_0_idx = e_mag.shape[1] // 2
    phi_90_idx = e_mag.shape[0] // 2
    # phi_0_idx = 0

    e_mag_norm_cut_p90 = 20 * np.log10(
        e_mag[phi_90_idx, :] / np.nanmax(e_mag[phi_90_idx, :])
    )
    e_mag_norm_cut_p0 = 20 * np.log10(
        e_mag[:, phi_0_idx] / np.nanmax(e_mag[:, phi_0_idx])
    )
    e_mag_norm_cut_p45 = 20 * np.log10(
        np.diagonal(e_mag) / np.nanmax(np.diagonal(e_mag))
    )

    theta_p90 = np.roll(yloc[phi_0_idx, :], +1)
    theta_p0 = np.roll(xloc[:, phi_90_idx], +1)
    theta_p45 = np.diagonal(np.roll(yloc, (0, +1))) * np.sqrt(2)

    # theta_p90 = yloc[phi_0_idx, :]
    # theta_p0 = xloc[:, phi_90_idx]
    # theta_p45 = theta_p90 * np.sqrt(2)

    # theta_p90 = np.roll(yloc[phi_0_idx, :], -0)
    # theta_p0 = np.roll(xloc[:, phi_90_idx], -0)
    # theta_p45 = np.diagonal(np.roll(yloc, (0,0))) * np.sqrt(2)

    # Values become unstable near horizon
    # Values become unstable near horizon
    theta_p90[np.abs(theta_p90) >= 180 - 0.001] = np.nan
    theta_p0[np.abs(theta_p0) >= 180 - 0.001] = np.nan
    theta_p45[np.abs(theta_p45) >= 180 - 0.1] = np.nan

    axs[1][0].plot(theta_p90, e_mag_norm_cut_p90, label="xNFT", marker=".")
    axs[0][0].plot(theta_p0, e_mag_norm_cut_p0, label="xNFT", marker=".")
    axs[2][0].plot(theta_p45, e_mag_norm_cut_p45, label="xNFT", marker=".")

    # axs[0][1].plot(theta_p0, np.angle(e_theta[:, phi_0_idx]), label='xNFT', marker='.')
    # axs[1][1].plot(theta_p90, np.angle(e_theta[phi_90_idx, :]), label='xNFT', marker='.')
    # axs[2][1].plot(theta_p45, np.angle(np.diagonal(e_theta)), label='xNFT', marker='.')

    # axs[0].plot(theta, e_mag[e_mag.shape[1]//2, :])
    # axs[0].set_ylim(0.01,None)
    # axs[0].set_xlim(-np.pi/2, np.pi/2)

    if far_field_data:

        e_mag_ff = np.linalg.norm(np.abs(far_field_data["E"]), ord=2, axis=0)

        print(
            f"FF Theta:\t[{np.min(far_field_data.theta.values) / np.pi}, "
            f"{np.max(far_field_data.theta.values) / np.pi}] π"
        )
        print(
            f"FF Phi:\t\t[{np.min(far_field_data.phi.values) / np.pi}, "
            f"{np.max(far_field_data.phi.values) / np.pi}] π"
        )

        theta_ff = far_field_data.theta
        phi_ff = far_field_data.phi

        phi_0_idx = 0
        phi_90_idx = phi_ff.size // 2
        phi_45_idx = phi_ff.size // 4

        e_mag_ff_norm = 20 * np.log10(
            e_mag_ff[:, :, f_idx] / np.max(e_mag_ff[:, :, f_idx])
        )

        axs[0][0].plot(
            theta_ff * 180 / np.pi,
            e_mag_ff_norm[phi_0_idx, :],
            label="Reference",
            marker=".",
        )
        # axs[0][0].plot(
        #     theta_ff,
        #     np.angle(
        #         far_field_data["E"].sel(component="theta")[phi_0_idx, :, f_idx]
        #     ),
        #     label="Reference",
        #     marker=".",
        # )
        # axs[1][0].plot(
        #     theta_ff,
        #     np.angle(
        #         far_field_data["E"].sel(component="theta")[
        #             phi_90_idx, :, f_idx
        #         ]
        #     ),
        #     label="Reference",
        #     marker=".",
        # )
        axs[1][0].plot(
            theta_ff * 180 / np.pi,
            e_mag_ff_norm[phi_90_idx, :],
            label="Reference",
            marker=".",
        )
        axs[2][0].plot(
            theta_ff * 180 / np.pi,
            e_mag_ff_norm[phi_45_idx, :],
            label="Reference",
            marker=".",
        )
        # axs[1].set_ylim(0,None)
        # axs[1].set_xlim(-np.pi/2, np.pi/2)

    axs[0][0].legend()

    axs[0][0].set_title(r"$\phi=0°$ Cut")
    axs[1][0].set_title(r"$\phi=90°$ Cut")
    axs[2][0].set_title(r"$\phi=45°$ Cut")

    for ax in axs:
        ax[0].set_ylabel(r"$|\mathbf{E}|$ (dB, Normalized)")
        ax[0].set_xlabel(r"Elevation ($\theta$)")
        ax[0].xaxis.set_major_formatter(fmt_deg)
        # ax[0].set_ylim(-np.pi, np.pi)
        ax[0].set_ylim(-60, 5)

    fig.tight_layout()
    plt.show()
