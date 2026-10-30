"""
Handle reading and writing xNFT projects.

xNFT projects store attributes/native Python as pickle files and arrays in

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

# Only imports Project for type checking
if TYPE_CHECKING:
    from .nodes.project import Project


def write_project(project: Project, compression_level=4):
    """
    Write `project` to disk in ZIP container (.xnft) format at specified `compression_level`.

    Parameters
    ----------
    project : Project
        Project to write to disk.
    compression_level : int, optional
        Gzip compression level (0-9) to use when writing datasets, by default 4.

    """

    if project._path is None:
        raise TypeError("Project path must be specified. Got `None`.")

    path = Path(project._path)
    tmp_dir = path.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)  # Make directories if needed

    # Temp file for atomic file replacements, keeping old save file if write fails midway
    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=".xnft") as tmp:
        tmp_path = Path(tmp.name)

    if compression_level > 9:
        compression_level = 9
    elif compression_level < 0:
        compression_level = 0

    try:
        project.to_zip(tmp_path, compression_level=compression_level)

        # atomic replace to avoid overwriting file with corrupted project
        os.replace(tmp_path, path)

    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def read_project(project_path: Path) -> Project:
    """
    Read project from `project_path` and return object.

    Parameters
    ----------
    project_path : Path
        Path to read project at.

    Returns
    -------
    Project
        Project loaded from disk.

    """
    # Force import of node modules to populate Node._registry via __init_subclass__
    from . import nodes  # noqa: F401
    from .nodes.node import Node
    from .nodes.project import Project

    path = Path(project_path).resolve()

    project = Node.from_zip(path)

    if not isinstance(project, Project):
        raise TypeError(f"Expected root node type Project, got type {type(project)}")

    # Update path if file name/path changed
    project.path = path

    return project
