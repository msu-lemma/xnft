"""
Handle xnft calibrations node actions.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from pathlib import Path
from PySide6.QtCore import QStandardPaths
import shutil
import logging
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import List

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import pandas as pd

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...project.nodes.fields import FieldNode

logger = logging.getLogger(__name__)

gain_cal_dir = (
    Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    / "calibrations"
    / "gain"
)


@dataclass
class GainCalibration:
    reference: GainCalibrationReference
    measurement: FieldNode


@dataclass
class GainCalibrationReference:
    manufacturer: str | None = None
    model: str | None = None
    serial: str | None = None
    data: pd.DataFrame | None = None

    @property
    def name(self):
        name_list = []
        if self.manufacturer not in (None, ""):
            name_list.append(self.manufacturer)
        if self.model not in (None, ""):
            name_list.append(self.model)
        if self.serial not in (None, ""):
            name_list.append(f"({self.serial})")
        return " ".join(name_list)


def copy_gain_cal_file(file_path):
    """Copy a gain cal file to the calibration file path."""

    src_file = Path(file_path)

    if src_file.suffix.lower() != ".cal":
        raise ValueError(f"Expected a .cal file, got '{src_file.name}'")

    calib_dir = gain_cal_dir
    dst_file = calib_dir / src_file.name

    shutil.copy2(src_file, dst_file)

    return dst_file


def load_gain_cal(path: str | Path, name_only: bool = False) -> GainCalibrationReference | str:
    """Load gain calibration files

    Parameters
    ----------
    path : str | Path
        File path to gain calibration file ".cal"
    name_only : bool, optional
        Return only the name contained int he file, don't parse entire file, by default False

    Returns
    -------
    GainCalibration | str
        GainCalibration or GainCalibration.name if "name_only" is True
    """
    gain_cal = GainCalibrationReference()

    with open(path, "r") as f:
        while True:
            # Store offest in bytes of start of line
            pos = f.tell()
            line = f.readline().strip()

            # Skip comments
            if line.startswith("#"):
                continue

            # Start of CSV header
            if "," in line and ":" not in line:
                # Move pointer back to the start of the line so read_csv parses the entire header
                f.seek(pos)
                break

            # Metadata
            if ":" in line:
                key, value = line.split(":", 1)

                try:
                    setattr(
                        gain_cal,
                        key.strip().lower(),
                        value.strip(),
                    )
                except AttributeError:
                    logger.warning(f"Metadata '{key}' not found in GainCalibration")

        if name_only:
            return gain_cal.name

        else:
            # read_csv will parse the rest of the file
            gain_cal.data = pd.read_csv(f)

            return gain_cal


def get_gain_cal_files(name_only):
    """Get gain cal files from calibration folder."""

    calib_dir = gain_cal_dir

    # If path doesn't exist, create it
    calib_dir.mkdir(parents=True, exist_ok=True)

    cal_files = sorted(calib_dir.glob("*.cal"))

    gain_files_available = []

    for cal_file in cal_files:
        gain_files_available.append((cal_file, load_gain_cal(cal_file, name_only=True)))

    return gain_files_available


def get_gain_correction(frequency: NDArray | float, interpolation: str | None = None):
    """Get gain correction value for a given input frequency.

    Parameters
    ----------
    frequency : NDArray or float
        Frequency or frequencies to get gain corrections for
    interpolation : str or None, optional
        Type of interpolation to use, by default None.
            'nearest': Use nearest gain calibration frequency
            'linear': Use linear interpolation between frequencies
            None: Return NaN for values not at calibrated values

    Return
    ------
    NDArray or float
        Gain value in dBi to be _added_ to gain to correct value
    """
    pass
