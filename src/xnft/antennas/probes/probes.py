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
                f"Probe source must be type MeasuredProbe or RectWaveguide, got {type(source)}."
            )

    def get_correction(self, phi_vec, theta_vec, wavelength):
        """
        Generate probe correction values to be applied via hadamard product to measurement array.
        """

        if self.correction_type == ProbeType.MEASURED:
            raise NotImplementedError("Measured probe corrections not yet implemented.")

        elif self.correction_type == ProbeType.IDEAL_RECT:
            # NOTE: Reverse phi vector rotation due to probe facing AUT
            print(f"{wavelength=}")
            co_pol_e_field = rect_e_far_field(
                ap_x=self.source.x,
                ap_y=self.source.y,
                wavelength_array=wavelength,
                phi_sample_vec=-phi_vec,
                theta_sample_vec=theta_vec,
                excitation="te10",
                apply_prop_const=False,
            )["E"]
            cx_pol_e_field = rect_e_far_field(
                ap_x=self.source.x,
                ap_y=self.source.y,
                wavelength_array=wavelength,
                phi_sample_vec=-phi_vec,
                rotation=np.pi / 2,
                theta_sample_vec=theta_vec,
                excitation="te10",
                apply_prop_const=False,
            )["E"]
            # Dims: ('component', 'phi', 'theta', 'frequency')

            # Reorder dimensions s.t. vector components is at the end
            co_pol_e_field = co_pol_e_field.transpose(
                "frequency", "phi", "theta", "component"
            ).values
            cx_pol_e_field = cx_pol_e_field.transpose(
                "frequency", "phi", "theta", "component"
            ).values

            logger.debug(f"{co_pol_e_field=}")

            co_pol_e_field = co_pol_e_field[..., [1, 0]]
            cx_pol_e_field = cx_pol_e_field[..., [1, 0]]

            r_mat = np.stack([co_pol_e_field, cx_pol_e_field], axis=-1)
            # Axis order: (frequency, phi, theta, polarization, component)

            r_mat_inv = np.linalg.inv(r_mat)

            # return r_mat
            return r_mat_inv
        else:
            raise TypeError(
                f"Probe source must be type MeasuredProbe or RectWaveguide, got {type(self.source)}."
            )
