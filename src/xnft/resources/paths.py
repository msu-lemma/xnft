"""
Handle loading paths from resource package in packaged executable.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from importlib.resources import files
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Return a path to a bundled resource."""
    return files("xnft.resources").joinpath(*parts)
