"""Core logic for xnft."""

import logging
import time

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants as spc

from numpy.fft import ifftn, ifftshift

# TODO: Add logic to detect if MLX is installed
# import mlx.core as mx
# import mlx.core.fft as mfft

from quantiphy import Quantity

from .. import __version__
from . import project

logger = logging.getLogger(__name__)


def nft(
    near_field_data, far_field_data, xfft_size=int(2**10), yfft_size=int(2**10)
):
    logger.debug(near_field_data)

    e_mag_nf = np.linalg.norm(np.abs(near_field_data["E"]) ** 2, ord=2, axis=0)

    t_start = time.perf_counter()
    e_x = near_field_data["E"].sel(component="x")
    e_y = near_field_data["E"].sel(component="y")
    # e_z = near_field_data["E"].sel(component='z')
    fe_x = ifftshift(
        ifftn(a=e_x, s=(xfft_size, yfft_size), axes=(0, 1)), axes=(0, 1)
    )
    fe_y = ifftshift(
        ifftn(a=e_y, s=(xfft_size, yfft_size), axes=(0, 1)), axes=(0, 1)
    )
    t_end = time.perf_counter()
    elapsed_time = Quantity(t_end - t_start, "s")
    logger.debug("np.fft: %s", elapsed_time)

    # Compute NFT iteratively for each frequency
    for f_idx, frequency in enumerate(np.nditer(near_field_data.frequency)):
        logger.debug(f"Frequency: {frequency * 1e-9:0.3f} GHz")

        wavelength = spc.c / frequency
        logger.debug(f"Wavelength: {wavelength * 1e3:0.3f} mm")

        xx, yy = np.meshgrid(near_field_data.x, near_field_data.y)

        k0 = 2.0 * np.pi / wavelength
        logger.debug(f"k0: {k0:0.3f} rad/m")

        Nx = near_field_data.x.size
        Ny = near_field_data.y.size

        x_length = (near_field_data.x.max() - near_field_data.x.min()).values
        y_length = (near_field_data.y.max() - near_field_data.y.min()).values

        print(f"x = {Quantity(x_length.item(), 'm')}")
        print(f"y = {y_length.item() * 1e3:0.3f} mm")

        kx = np.linspace(-Nx / 2, Nx / 2, xfft_size) * 2.0 * np.pi / x_length
        ky = np.linspace(-Ny / 2, Ny / 2, yfft_size) * 2.0 * np.pi / y_length
        kz = np.sqrt(k0**2 - kx**2 - ky**2)

        print(f"{kx=} rad/m")
        print(f"{ky=} rad/m")
        print(f"{kz=} rad/m")

        kxx, kyy = np.meshgrid(kx, ky)
        kzz = np.emath.sqrt(k0**2 - kxx**2 - kyy**2).real

        # Compute spherical wavefront angles
        phi_grid = np.atan2(kyy, kxx)
        theta_grid = np.arccos(kzz / k0)

        # Focus energy back to source plane
        fe_x[:, :, 0, f_idx] *= np.exp(
            1.0j * kzz * near_field_data.z.values[0]
        )
        fe_y[:, :, 0, f_idx] *= np.exp(
            1.0j * kzz * near_field_data.z.values[0]
        )

        fe_z = -(fe_x[:, :, 0, f_idx] * kxx + fe_y[:, :, 0, f_idx] * kyy) / kzz
        fe_z *= np.exp(1.0j * kzz * near_field_data.z.values[0])

        # Compute magnitude of E-field to plot
        e_mag = np.sqrt(
            np.abs(fe_x[:, :, 0, f_idx]) ** 2
            + np.abs(fe_y[:, :, 0, f_idx]) ** 2
            + np.abs(fe_z) ** 2
        )

        fig, axs = plt.subplots(3, 1, figsize=(6, 12))

        axs[0].pcolormesh(
            xx,
            yy,
            e_mag_nf[:, :, 0, f_idx],
        )
        axs[0].set_aspect("equal")

        print(
            f"Theta:\t[{np.min(theta_grid) / np.pi}, {np.max(theta_grid) / np.pi}] π"
        )
        print(
            f"Phi:\t[{np.min(phi_grid) / np.pi}, {np.max(phi_grid) / np.pi}] π"
        )

        # Convert polar to cartesian to plot on pcolormesh
        xloc = theta_grid * np.cos(phi_grid)
        yloc = theta_grid * np.sin(phi_grid)

        # axs[1].pcolormesh(xloc, yloc, e_mag, )
        axs[1].pcolormesh(
            kxx,
            kyy,
            e_mag,
        )

        axs[1].set_aspect("equal")

        e_mag_ff = np.linalg.norm(
            np.abs(far_field_data["E"]) ** 2, ord=2, axis=0
        )

        print(
            f"FF Theta:\t[{np.min(far_field_data.theta.values) / np.pi}, {np.max(far_field_data.theta.values) / np.pi}] π"
        )
        print(
            f"FF Phi:\t\t[{np.min(far_field_data.phi.values) / np.pi}, {np.max(far_field_data.phi.values) / np.pi}] π"
        )

        ff_theta = far_field_data.theta - np.pi / 2
        ff_phi = far_field_data.phi

        # xloc = theta * np.cos(far_field_data.phi)
        # yloc = theta * np.sin(far_field_data.phi)
        # yloc = np.cos(far_field_data.theta)
        # xloc = np.sin(far_field_data.phi)
        xloc = far_field_data.phi
        yloc = ff_theta

        # xloc = ff_theta * np.cos(far_field_data.phi)
        # yloc = ff_theta * np.sin(far_field_data.phi)

        # xloc[far_field_data.theta > np.pi / 2] = np.nan
        # yloc[far_field_data.theta > np.pi / 2] = np.nan

        emag = e_mag_ff[:, :, f_idx]
        emag[((ff_theta**2 + ff_phi**2) ** 0.5 > 0.5 * np.pi)] = np.nan

        axs[2].pcolormesh(xloc, yloc, 10 * np.log10(emag))
        axs[2].set_aspect("equal")

        # plt.show()

        break
