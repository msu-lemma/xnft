"""
Standard waveguide probe dimensions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from enum import Enum

from xnft.antennas.aperture.rectangular import RectWaveguide


class StandardRectWaveguide(Enum):
    WR770 = RectWaveguide(195.6e-3, 97.79e-3, (0.97e9, 1.45e9))
    WR640 = RectWaveguide(165.1e-3, 82.55e-3, (1.15e9, 1.72e9))
    WR510 = RectWaveguide(129.5e-3, 64.77e-3, (1.45e9, 2.20e9))
    WR430 = RectWaveguide(109.2e-3, 54.61e-3, (1.72e9, 2.60e9))
    WR340 = RectWaveguide(86.36e-3, 43.18e-3, (2.20e9, 3.30e9))
    WR284 = RectWaveguide(72.14e-3, 34.94e-3, (2.60e9, 3.95e9))
    WR229 = RectWaveguide(58.17e-3, 29.08e-3, (3.30e9, 4.90e9))
    WR187 = RectWaveguide(47.55e-3, 22.2e-3, (3.95e9, 5.85e9))
    WR159 = RectWaveguide(40.38e-3, 20.2e-3, (4.90e9, 7.05e9))
    WR137 = RectWaveguide(34.90e-3, 15.8e-3, (5.85e9, 8.20e9))
    WR112 = RectWaveguide(28.50e-3, 12.6e-3, (7.05e9, 10.0e9))
    WR90 = RectWaveguide(22.9e-3, 10.2e-3, (8.2e9, 12.4e9))
    WR75 = RectWaveguide(19.1e-3, 9.53e-3, (10.0e9, 15.0e9))
    WR62 = RectWaveguide(15.8e-3, 7.90e-3, (12.4e9, 18.0e9))
    WR51 = RectWaveguide(13.0e-3, 6.48e-3, (15e9, 22e9))
    WR42 = RectWaveguide(10.7e-3, 4.32e-3, (18e9, 26.5e9))
    WR34 = RectWaveguide(8.64e-3, 4.32e-3, (22e9, 33e9))
    WR28 = RectWaveguide(7.11e-3, 3.56e-3, (26.5e9, 40e9))
    WR22 = RectWaveguide(5.68e-3, 2.84e-3, (33e9, 50e9))
    WR19 = RectWaveguide(4.78e-3, 2.39e-3, (40e9, 60e9))
    WR15 = RectWaveguide(3.76e-3, 1.88e-3, (50e9, 75e9))
    WR12 = RectWaveguide(3.10e-3, 1.55e-3, (60e9, 90e9))
    WR10 = RectWaveguide(2.54e-3, 1.27e-3, (75e9, 110e9))
    WR8 = RectWaveguide(2.03e-3, 1.02e-3, (90e9, 140e9))
    # NOTE: WR6, WR6.5 and WR7 are identical sizes
    WR7 = RectWaveguide(1.65e-3, 0.826e-3, (110e9, 170e9))
    WR6 = RectWaveguide(1.65e-3, 0.826e-3, (110e9, 170e9))  # noqa: PIE796
    WR5 = RectWaveguide(1.30e-3, 0.648e-3, (140e9, 220e9))
    WR4 = RectWaveguide(1.09e-3, 0.546e-3, (170e9, 260e9))
    WR3 = RectWaveguide(0.864e-3, 0.432e-3, (220e9, 330e9))
