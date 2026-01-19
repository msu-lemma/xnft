"""
Module providing structured type enumerations.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""
from enum import StrEnum


class NodeType(StrEnum):
    """Available project node types."""
    PROJECT = "Project"
    FIELDS = "Fields"
    ANALYSIS = "Analysis"
    COORDINATES = "Coordinates"
    RESTULTS = "Results"
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


class CoordinateSystem(StrEnum):
    """Available coordinate system types."""
    CARTESIAN = "Cartesian"
    CYLINDRICAL = "Cylindrical"
    SPHERICAL = "Spherical"
    UNKNOWN = "Unknown"


class AnalysisType(StrEnum):
    """Available analysis types."""
    TRANSFORM = "Transform"
    INTERPOLATION = "Interpolation"
    UNKNOWN = "Unknown"


class DataSourceType(StrEnum):
    """Available source file types."""
    XNFT = "xNFT"
    THEORY = "Theoretical Ideal Aperture"
    HFSS = "Ansys HFSS"
    NSI_MEAS = "NSI-MI Scanner Measurement"
    NSI_REF = "NSI-MI Scanner Reference"
    LEMMA = "LEmmA Scanner Measurement"
