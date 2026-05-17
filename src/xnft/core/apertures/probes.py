"""
Measurement probe class.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from ..enums import ProbeType
from .rectangular import RectWaveguide


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


class MeasuredProbe:
    pass
