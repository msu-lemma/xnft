"""
Module providing structured type enumerations.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from enum import StrEnum


class NodeType(StrEnum):
    """Available project node types."""

    PROJECT = "Project"
    FIELDS = "Fields"
    ANALYSIS = "Analysis"
    COORDINATES = "Coordinates"
    RESULTS = "Results"
    MODEL = "Model"
    UNKNOWN = "Unknown"


class ReportType(StrEnum):
    """Available report types."""

    PLOT_1D = "1D Plot"
    PLOT_2D = "2D Plot"
    PLOT_3D = "3D Plot"
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


class CoordinateSystemType(StrEnum):
    """Available coordinate system types."""

    CARTESIAN = "Cartesian"
    CYLINDRICAL = "Cylindrical"
    SPHERICAL = "Spherical"
    DIRECTION_COSINE = "Direction Cosine (u,v)"
    SPHERICAL_AZEL = "Azimuth/Elevation"
    UNKNOWN = "Unknown"


class AnalysisType(StrEnum):
    """Available analysis types."""

    TRANSFORM = "Transform"
    INTERPOLATION = "Interpolation"
    UNKNOWN = "Unknown"


class DataSourceType(StrEnum):
    """Available source file types."""

    XNFT = "xNFT"
    THEORY = "Ideal Aperture"
    HFSS = "Ansys HFSS"
    NSI_MEAS = "NSI-MI Scanner"
    NSI_REF = "NSI-MI Reference"
    LEMMA = "LEmmA Scanner"


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


class Units(StrEnum):
    METERS = "m"
    RADIANS = "rad"
    DEGREES = "deg"