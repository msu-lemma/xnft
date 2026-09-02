"""
Module providing specialized types.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from pathlib import Path
from typing import NamedTuple

from .enums import PolarizationType, SParameterType


class FileInfo(NamedTuple):
    """
    File path and metatdata struct.

    Parameters
    ----------
    path : pathlib.Path
        Path to file.
    polarization : PolarizationTye or Set[PolarizationType], optional
        Polarization of data stored in file, may be a typle of both co-
        and cross-pol, by default {PolarizationType.CO_POL, PolarizationType.CROSS_POL}
    s_parameters : Set[SParameterType]
        S-Parameter in file to load for processing
    """

    path: Path
    polarization: PolarizationType | set[PolarizationType] = {
        PolarizationType.CO_POL,
        PolarizationType.CROSS_POL,
    }
    s_parameters: set[SParameterType] = set()
