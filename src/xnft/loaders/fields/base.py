"""
Common field loader information.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass


@dataclass
class LoaderInfo:
    id: str
    name: str
    extensions: list[str]
    source_type: str
