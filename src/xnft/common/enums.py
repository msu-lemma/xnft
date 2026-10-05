"""
Module providing structured type enumerations.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from collections import namedtuple
from enum import Enum, StrEnum

import unyt

CoordinateSystemTuple = namedtuple("CoordinateSystemTuple", ["name", "components"])


class NodeType(StrEnum):
    """Available project node types."""

    PROJECT = "Project"
    FIELDS = "Fields"
    PROBES = "Probes"
    CALS = "Calibrations"
    ANALYSIS = "Analysis"
    COORDINATES = "Coordinates"
    REPORTS = "Reports"
    MODEL = "Model"
    UNKNOWN = "Unknown"


class ProbeType(StrEnum):
    """Available measurement probe types."""

    IDEAL_RECT = "Ideal Rectangular Probe"
    MEASURED = "Measured Probe"
    UNKNOWN = "Unknown"


class ReportType(StrEnum):
    """Available report types."""

    PLOT_LINE = "Line Plot"
    PLOT_SURFACE_2D = "2D Surface Plot"
    PLOT_SURFACE_3D = "3D Surface Plot"
    TABLE = "Table"
    UNKNOWN = "Unknown"


class FieldType(StrEnum):
    """Available field types."""

    NEAR = "Near Field"
    FAR = "Far Field"
    UNKNOWN = "Unknown"


class ScanType(StrEnum):
    """Available scan types."""

    PLANAR = "Planar"
    CYLINDRICAL = "Cylindrical"
    SPHERICAL = "Spherical"
    UNKNOWN = "Unknown"


class CoordinateSystemType(Enum):
    """Available coordinate system types."""

    CARTESIAN = CoordinateSystemTuple(
        name="Cartesian (x,y,z)",
        components=("x", "y", "z"),
    )
    CYLINDRICAL = CoordinateSystemTuple(
        name="Cylindrical (ρ,φ,z)",
        components=("rho", "phi", "z"),
    )
    SPHERICAL = CoordinateSystemTuple(
        name="Spherical (r,θ,φ)",
        components=("r", "theta", "phi"),
    )
    DIRECTION_COSINE = CoordinateSystemTuple(
        name="Direction Cosine (u,v)", components=("u", "v")
    )
    SPHERICAL_AZEL = CoordinateSystemTuple(
        name="Azimuth/Elevation", components=("az", "el")
    )
    UNKNOWN = CoordinateSystemTuple(name="Unknown", components=())


class AnalysisType(StrEnum):
    """Available analysis types."""

    PLANAR_TRANSFORM = "Planar Near Field Transform"
    SPHERICAL_TRANSFORM = "Spherical Near Field Transform"
    UNKNOWN = "Unknown"


class DataPolarizationType(StrEnum):
    """
    Specifies which polarizations are expected in a file.

    SINGLE_POL: Single polarization measurement is stored in the file
    COMBOL_POL: Both polarizations are stored in the file
    """

    SINGLE_POL = "Single Polarization"
    COMBO_POL = "Combined Polarization"


class SParameterType(StrEnum):
    """Possible S-Parameters for VNA measurements."""

    S11 = "S11"
    S12 = "S12"
    S21 = "S21"
    S22 = "S22"


class PolarizationType(StrEnum):
    """Polarizations."""

    CO_POL = "Co-Polarization"
    CROSS_POL = "Cross-Polarization"


class Scale(StrEnum):
    """Data scaling."""

    LINEAR = "Linear"
    DB = "Decibels"


class Unit(Enum):
    METERS = unyt.meter
    RADIANS = unyt.radian
    DEGREES = unyt.degree
    HERTZ = unyt.hertz
    VOLTS = unyt.volt
    AMPERES = unyt.ampere
    HENRYS = unyt.henry
