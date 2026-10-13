"""
Measurement probe class.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging

import numpy as np

from ...common.enums import ProbeType
from ..aperture.rectangular import RectWaveguide, rect_e_far_field

logger = logging.getLogger(__name__)


class MeasuredProbe:
    def __init__(self, ap_x, ap_y):
        self.x = ap_x
        self.y = ap_y


class MeasurementProbe:
    """
    Class for handling measurmenet probe sampling and numerical operations.

    This object may contain either an ideal theoretical aperture description, or a measured
    probe dataset.  In the measured probe dataset, an interpolation must be performed to
    obtain the exact sample locations desired for probe corrections in the far field.

    Parameters
    ----------
    name : str
        A friendly name to display to the user.
    source : MeasuredProbe | RectWaveguide
        The source object for the measurement probe.  May be either a measured probe file, or a
        theoretical ideal aperture. Presently, only rectangular waveguide apertures are supported.

    Raises
    ------
    TypeError
        Probe source type must be MeasuredProbe or RectWaveguide

    """

    def __init__(self, name: str, source: MeasuredProbe | RectWaveguide) -> None:

        self.name = name
        self.source = source

        self.correction_type = ProbeType.UNKNOWN
        if isinstance(source, MeasuredProbe):
            self.correction_type = ProbeType.MEASURED
        elif isinstance(source, RectWaveguide):
            self.correction_type = ProbeType.IDEAL_RECT
        else:
            raise TypeError(
                f"Probe source must be type MeasuredProbe or RectWaveguide, got {type(source)}.",
            )

    def get_reception_matrix(self, theta_vec, phi_vec, wavenumber):
        """Generate probe reception matrix values."""
        if self.correction_type == ProbeType.MEASURED:
            raise NotImplementedError("Measured probe corrections not yet implemented.")

        if self.correction_type == ProbeType.IDEAL_RECT:
            wavelength = 2.0 * np.pi / wavenumber

            print(f"{wavelength=}")
            # x-oriented probe
            x_pol_e_field = rect_e_far_field(
                ap_x=self.source.x,
                ap_y=self.source.y,
                wavelength_array=wavelength,
                theta_sample_vec=theta_vec,
                phi_sample_vec=phi_vec,
                rotation=-np.pi / 2,  # Rotate clockwise 90° about the z-axis
                flip_x=False,
                flip_y=True,  # Flip pattern 180° about y-axis
                excitation="te10",
                apply_prop_const=False,
            )["E"]

            # y-oriented probe
            y_pol_e_field = rect_e_far_field(
                ap_x=self.source.x,
                ap_y=self.source.y,
                wavelength_array=wavelength,
                theta_sample_vec=theta_vec,
                phi_sample_vec=phi_vec,
                flip_x=False,
                flip_y=True,  # Flip pattern 180° about y-axis
                excitation="te10",
                apply_prop_const=False,
            )["E"]
            # Dims: ('component', 'theta', 'phi', 'frequency')

            # Reorder dimensions s.t. vector components is at the end
            x_pol_e_field = x_pol_e_field.transpose(
                "frequency",
                "theta",
                "phi",
                "component",
            ).values
            y_pol_e_field = y_pol_e_field.transpose(
                "frequency",
                "theta",
                "phi",
                "component",
            ).values

            r_mat = np.stack([x_pol_e_field, y_pol_e_field], axis=-2)
            # Axis order: (frequency, theta, phi, polarization, component)

            r_mat_inv = np.linalg.inv(r_mat)

            return r_mat_inv
        raise TypeError(
            f"Probe source must be type MeasuredProbe or RectWaveguide, got {type(self.source)}.",
        )
