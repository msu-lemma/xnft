"""
Field transform algorithms.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

import logging
import time
import warnings
from collections.abc import Callable

import finufft
import numpy as np
import scipy.constants as spc
import xarray as xr
from quantiphy import Quantity
from scipy.signal import windows

from ..antennas.probes.probes import MeasurementProbe

# from numpy.typing import ArrayLike
from ..common.enums import CoordinateSystemType, FieldType
from ..common.registry import registry
from ..common.types import FieldDataset
from ..project.nodes.calibrations import GainCalibrationNode

logger = logging.getLogger(__name__)


def calibrate_gain(
    field: xr.Dataset, gain_calibration: GainCalibrationNode
) -> xr.Dataset:
    """Apply gain calibrations to field."""
    result_field = field.copy(deep=True)

    gain_cal_table = gain_calibration.gain_cal_ref.data
    gain_cal_meas_field = gain_calibration.gain_cal_field.data

    logger.debug(f"{gain_cal_table=}")

    # Configure gain cal interpolation across frequencies
    gain_reference_interp = gain_cal_table.interp(
        frequency=field.frequency,  # NOTE: frequency may be a vector of frequencies
        method="linear",
    )

    # Take gain of measured aut field over phi/theta dimensions (max per frequency)
    gain_meas_aut = 10 * np.log10(
        ((np.abs(field["E"]) ** 2).sum(dim="component")).max(dim=("theta", "phi"))
    )

    logger.debug(f"{gain_meas_aut=}")

    # Take gain of reference antenna measured field over phi/theta dimensions (max per frequency)
    gain_meas_ref = 10 * np.log10(
        ((np.abs(gain_cal_meas_field["E"]) ** 2).sum(dim="component")).max(
            dim=("theta", "phi")
        )
    )

    logger.debug(f"{gain_meas_ref=}")

    # Correction value to add to our AUT measured field (in dB)
    gain_correction_db = gain_reference_interp - gain_meas_ref
    logger.debug(f"{gain_correction_db=}")

    gain_correction = 10 ** (gain_correction_db / 20)

    # logger.debug(f"{gain_correction=}")

    # Convert from power gain back to linear amplitude gain
    result_field["E"] = field["E"] * gain_correction

    logger.debug(f"{result_field=}")

    return result_field


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
    z_val,
    r_far_field: float | None = None,
    probe_correction: MeasurementProbe | None = None,
):
    r"""
    Compute the planar near-to-far field transform for a single frequency

    Parameters
    ----------
    theta_grid_target : ArrayLike
        2D grid of theta sample points for output.
    phi_grid_target : ArrayLike
        2D phi of theta sample points for output.
    k0 : float
        Wavenumber to compute output for
    win : ArrayLike
        2D windowing function to apply to input field.
    near_field_x_scaled : ArrayLike
        Displacement along x-axis, normalized from -pi/2,pi/2 for NUFFT
    near_field_y_scaled : ArrayLike
        Displacement along y-axis, normalized from -pi/2,pi/2 for NUFFT
    x_scale : float
        Scaling factor for x-component for NUFFT
    y_scale : float
        Scaling factor for x-component for NUFFT
    e_x : ArrayLike
        E-field x-component
    e_y : ArrayLike
        E-field y-component
    z_val : float
        Z-height above AUT samples collected at (in meters)
    r_far_field : float or None, optional
        Far-field radius compute transform at, by default None
    probe_correction : MeasurementProbe or None, optional
        Probe correction fields to use, if any, by default None

    Returns
    -------
    Tuple[ArrayLike]
        Tuple of $E_\\mathrm{phi}$ and $E_\\mathrm{theta}$ fields

    """
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

    target_shape = theta_grid_target.shape
    fe_x = plan.execute(field_values_x).reshape(target_shape)
    fe_y = plan.execute(field_values_y).reshape(target_shape)

    if probe_correction:
        # Apply corrections in k-space
        fe_mat = np.stack([fe_x, fe_y], axis=-1)

        # reception_mat_inv is in (theta, phi)
        reception_mat_inv = probe_correction.get_reception_matrix(
            theta_vec=theta_grid_target[:, 0],
            phi_vec=phi_grid_target[0, :],
            wavenumber=k0,
        )[0]  # remove frequency axis [0] that is always of size 1

        logger.debug(f"{reception_mat_inv.shape=}")
        logger.debug(f"{fe_mat.shape=}")

        # Perform matrix multiplication of R^-1 matrix and E-field
        # Probe compensation matrix include transform to spherical
        e_mat = (reception_mat_inv @ fe_mat[..., np.newaxis])[..., 0]

        # Add propagation phase to probe
        # TODO: make this correction optional
        e_mat *= np.exp(1j * k0 * z_val * np.cos(theta_grid_target[..., np.newaxis]))

    else:
        e_theta = fe_x * np.cos(phi_grid_target) + fe_y * np.sin(phi_grid_target)
        e_phi = np.cos(theta_grid_target) * (
            -fe_x * np.sin(phi_grid_target) + fe_y * np.cos(phi_grid_target)
        )
        e_mat = np.stack([e_theta, e_phi], axis=-1)

    # Apply propagation constants
    # Phase correction term such that phase at measured radius is constant
    if r_far_field is not None:
        greens_func = np.exp(-1j * k0 * r_far_field) / r_far_field
        c0 = 1j * k0 / (2.0 * np.pi) * greens_func
        e_mat *= c0

    return e_mat


def planar_near_field_transform(
    near_field: xr.Dataset,
    frequencies: np.ndarray | list[float] | None = None,
    probe_correction: MeasurementProbe | None = None,
    gain_calibration: GainCalibrationNode | None = None,
    dphi: float = 1.0,
    dtheta: float = 1.0,
    window: Callable = windows.boxcar,
    r_far_field=None,  # meters
    z_displacement=None,
) -> xr.Dataset:
    """
    Compute the near to far-field transform via non-uniform fast Fourier transform (NUFFT).

    The NUFFT performed here uses the fiNUFFT package [1]_, [2]_, [3]_. The plnar near-to-far field transform
    implementation proceeds from Ch 12.9 [4]_ and the derivation included in the documentation.

    Parameters
    ----------
    near_field : xr.Dataset
        Planar near-field measured values to transform to far-field.
    frequencies : np.ndarray | List[float] | None
        Frequencies in Hertz to perform the near-to-far field transform at.  If the provided frequency is not
        found in the `near_field` input, the nearest frequency present will be used instead and a warning will
        be raised to the user.
    probe_correction : MeasurementProbe or None, optional
        Probe correction fields to use, if any, by default None
    dphi : int, optional
        Phi step size, by default 1.0 degrees
    dtheta : int, optional
        Theta step size, by default 1.0 degrees
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
    .. [1] fiNUFFT Mathematical definitions of transforms. Online: https://finufft.readthedocs.io/en/latest/math.html

    .. [2] A. H. Barnett, J. F. Magland, and L. af Klinteberg, A parallel non-uniform fast Fourier transform library
        based on an “exponential of semicircle” kernel. SIAM J. Sci. Comput. 41(5), C479-C504 (2019).
        Online: https://arxiv.org/abs/1808.06736

    .. [3] A. H. Barnett, Aliasing error of the exp(𝛽√1-z2) kernel in the nonuniform fast Fourier transform.  Appl.
        Comput. Harmon. Anal. 51, 1-16 (2021). Online: https://arxiv.org/abs/2001.09405

    .. [4] C. A. Balanis, Antenna theory: analysis and design, 3. ed. Hoboken, N.J: Wiley-Interscience, 2005.

    """
    near_field_e = near_field["E"]

    freq = near_field_e.frequency

    # Normalize once
    if freq.ndim == 0:
        freq_values = np.atleast_1d(freq.item())
    else:
        freq_values = freq.values

    logger.debug(
        "Available frequencies: %s",
        ", ".join(str(Quantity(x, "Hz")) for x in freq_values),
    )

    if frequencies is None:
        frequencies = freq_values

    # Compute maximum valid elevation angle to be used in computation (limited by sample locations and aperture sizes)
    aut_size = near_field.attrs["aperture_size"]

    # If a probe is specified, get probe size for valid angle computation, otherwise assume zero size
    if probe_correction is not None:
        probe_size = (
            probe_correction.source.x**2 + probe_correction.source.y**2
        ) ** 0.5
    else:
        probe_size = 0

    logger.debug(f"AUT Size: {Quantity(aut_size, units='m')}")
    logger.debug(f"Probe Size: {Quantity(probe_size, units='m')}")

    # Conservative values
    min_x_displacement = min(np.abs(np.min(near_field.x)), np.max(near_field.x))
    min_y_displacement = min(np.abs(np.min(near_field.y)), np.max(near_field.y))

    if z_displacement is not None:
        max_z_displacement = z_displacement
    else:
        max_z_displacement = np.max(np.abs(near_field.z))

    logger.debug(f"min_x_displacement: {Quantity(min_x_displacement, units='m')}")
    logger.debug(f"min_y_displacement: {Quantity(min_y_displacement, units='m')}")
    logger.debug(f"max_z_displacement: {Quantity(max_z_displacement, units='m')}")

    max_aperture_displacement = min(min_x_displacement, min_y_displacement) - (
        aut_size / 2
    )  # - (probe_size / 2)
    logger.debug(
        f"max_aperture_displacement: {Quantity(max_aperture_displacement, units='m')}",
    )

    max_theta = np.atan2(max_aperture_displacement, max_z_displacement).values.squeeze()
    logger.debug(f"Max. Theta: {Quantity(max_theta * 180 / np.pi)}°")

    # Compute uniform Theta, Phi grid for target field points
    theta_target = np.linspace(
        -np.pi / 2,
        np.pi / 2,
        round(np.pi / np.deg2rad(dtheta)) + 1,
        endpoint=True,
    )
    phi_target = np.linspace(
        -np.pi / 2,
        np.pi / 2,
        round(np.pi / np.deg2rad(dphi)) + 1,
        endpoint=True,
    )

    # Trim theta
    theta_target = theta_target[
        (theta_target >= -max_theta) & (theta_target <= max_theta)
    ]

    theta_grid_target, phi_grid_target = np.meshgrid(
        theta_target,
        phi_target,
        indexing="ij",
    )

    # Generate windowing function (rectangular by default)
    win_x = window(near_field_e.x.size)
    win_y = window(near_field_e.y.size)

    # Normalize window
    win = np.sqrt(np.outer(win_x, win_y))

    # Scale source sample locations along aperture to input of finufft in the range [-pi/2, pi/2)
    x_scale = (
        2.0 * np.pi / (np.max(near_field_e.x.values) - np.min(near_field_e.x.values))
    )
    y_scale = (
        2.0 * np.pi / (np.max(near_field_e.y.values) - np.min(near_field_e.y.values))
    )

    near_field_yy, near_field_xx = np.meshgrid(
        near_field_e.y.values,
        near_field_e.x.values,
    )

    near_field_x_scaled = (x_scale * near_field_xx).ravel()
    near_field_y_scaled = (y_scale * near_field_yy).ravel()

    # Start performance timer
    t_start = time.perf_counter()

    # Generate parallel function call arguments
    args_list = []
    z_val = near_field_e.coords["z"].item()  # should only have one z-height value

    # Ensure frequencies is an array (if scalar)
    frequencies = np.array(frequencies)

    for freq in np.nditer(frequencies):
        f_idx = np.argmin(np.abs(freq_values - freq))
        nearest_freq = freq_values[f_idx]

        if nearest_freq != freq:
            warnings.warn(
                "Provided frequency {:} not in available frequencies, using nearest frequency {:} instead".format(
                    Quantity(freq, "Hz"),
                    Quantity(nearest_freq, "Hz"),
                ),
            )
            freq = nearest_freq

        wavelength = spc.c / freq
        k0 = 2.0 * np.pi / wavelength

        # Load E-field data from dataset
        # Dimensions (x, y, z, freq)
        if near_field_e.frequency.ndim == 1:
            e_x = near_field_e.sel(component="x", frequency=freq, z=z_val).values
            e_y = near_field_e.sel(component="y", frequency=freq, z=z_val).values
        else:
            e_x = near_field_e.sel(component="x", z=z_val).values
            e_y = near_field_e.sel(component="y", z=z_val).values

        args_list.append(
            {
                "theta_grid_target": theta_grid_target,
                "phi_grid_target": phi_grid_target,
                "k0": k0,
                "win": win,
                "near_field_x_scaled": near_field_x_scaled,
                "near_field_y_scaled": near_field_y_scaled,
                "x_scale": x_scale,
                "y_scale": y_scale,
                "e_x": e_x,
                "e_y": e_y,
                "z_val": z_val,
                "r_far_field": r_far_field,
                "probe_correction": probe_correction,
            },
        )

    # Call planar near-field transform in parallel
    # NOTE: it's faster to not run in parallel (Observed on macOS;
    #       performance appears much slower on other platforms, unsure if parallel would be faster)
    # e_mat_list = Parallel(n_jobs=-1, backend="multiprocessing", verbose=10)(
    #     delayed(planar_near_field_transform_t3)(**args) for args in args_list
    # )
    e_mat_list = [planar_near_field_transform_t3(**args) for args in args_list]

    # Print ellapsed time
    elapsed_time = Quantity(time.perf_counter() - t_start, "s")
    logger.debug(f"Far-field transform: {elapsed_time}")

    # Generate field output
    # Reorder output to: (component, theta, phi, frequency)
    e_field = np.transpose(e_mat_list, (3, 1, 2, 0))

    fields = FieldDataset.create(
        e_field=e_field,
        spatial_coords={
            "theta": theta_target,
            "phi": phi_target,
        },
        frequency=frequencies,
        coordinate_system=CoordinateSystemType.SPHERICAL,
        field_type=FieldType.FAR,
        data_source=registry.data_sources.get("xnft"),
        aperture_size=near_field.attrs["aperture_size"],
        gain_calibration=gain_calibration,
    )

    # Compute gain calibration if provided
    if gain_calibration is not None:
        fields = calibrate_gain(fields, gain_calibration)

    return fields
