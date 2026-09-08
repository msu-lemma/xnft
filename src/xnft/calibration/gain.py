"""
Handle xnft calibrations node actions.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import xarray as xr
from numpy.typing import NDArray
from PySide6.QtCore import QStandardPaths

if TYPE_CHECKING:
    from ..project.nodes.fields import FieldNode  # noqa: TC004

logger = logging.getLogger(__name__)

gain_cal_dir = (
    Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    / "calibrations"
    / "gain"
)


@dataclass
class GainCalibrationReference:
    manufacturer: str | None = None
    model: str | None = None
    serial: str | None = None
    data: xr.DataArray | None = None

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


@dataclass
class GainCalibration:
    reference: GainCalibrationReference
    measurement: FieldNode


def copy_gain_cal_file(file_path):
    """Copy a gain cal file to the calibration file path."""

    src_file = Path(file_path)

    if src_file.suffix.lower() not in (".cal", ".ngt"):
        raise ValueError(f"Expected a .cal or .ngt file, got '{src_file.name}'")

    calib_dir = gain_cal_dir
    dst_file = calib_dir / src_file.name

    shutil.copy2(src_file, dst_file)

    logger.info(f"Wrote gain calibration file to: {dst_file}")

    return dst_file


def load_gain_cal(
    path: str | Path, name_only: bool = False
) -> GainCalibrationReference | str:
    """Load gain calibration files

    Parameters
    ----------
    path : str | Path
        File path to gain calibration file ".cal" or ".ngt"
    name_only : bool, optional
        Return only the name contained int he file, don't parse entire file, by default False

    Returns
    -------
    GainCalibration | str
        GainCalibration or GainCalibration.name if "name_only" is True
    """
    gain_cal = GainCalibrationReference()

    path = Path(path)

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
            return path.stem if gain_cal.name == "" else gain_cal.name

        else:
            # read_csv will parse the rest of the file
            df = pd.read_csv(f)
            df.columns = df.columns.str.strip()

            logger.debug(df)

            # Get file type
            if path.suffix == ".cal":
                # Convert dataframe to DataArray for interpolation
                gain_cal.data = xr.DataArray(
                    df["gain_dbi"].to_numpy(),
                    coords={
                        "frequency": df["frequency_hz"].to_numpy(),
                    },
                    dims=("frequency",),
                    name="gain_ref",
                    attrs={"units": "dBi"},
                )

            elif path.suffix == ".ngt":
                # Convert dataframe to DataArray for interpolation
                df["Freq"] *= 1e9  # convert to Hertz
                gain_cal.data = xr.DataArray(
                    df["Gain"].to_numpy(),
                    coords={
                        "frequency": df["Freq"].to_numpy(),
                    },
                    dims=("frequency",),
                    name="gain_ref",
                    attrs={"units": "dBi"},
                )

            else:
                raise NotImplementedError(f"File type {path.suffix} is not supported.")

            return gain_cal


def get_gain_cal_files(name_only):
    """Get gain cal files from calibration folder."""

    calib_dir = gain_cal_dir

    # If path doesn't exist, create it
    calib_dir.mkdir(parents=True, exist_ok=True)

    cal_files = sorted(list(calib_dir.glob("*.cal")) + list(calib_dir.glob("*.ngt")))

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
