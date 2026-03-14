"""
Handle reading and writing xNFT projects.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""
from compression import zstd
import pickle
from pathlib import Path
from typing import TYPE_CHECKING

# Only imports Projec tfor type checking
if TYPE_CHECKING:
    from .nodes.project import Project


def write_project(project: Project, compression_level=10):
    """Write `project` to disk at specified `compression_level`.

    Parameters
    ----------
    project : Project
        Project to write to disk.
    compression_level : int, optional
        Compression level for `zstd` to use when writing, by default 10.
    """
    if project._path is not None:
        with zstd.open(project._path, mode="wb", level=compression_level) as f:
            pickle.dump(project, f)
    else:
        raise TypeError('Project path must be specified. Got `None`.')


def read_project(project_path: Path) -> Project:
    """Read project from `project_path` and return object.

    Parameters
    ----------
    project_path : Path
        Path to read project at.

    Returns
    -------
    Project
        Project loaded from disk.
    """
    with zstd.open(project_path, "rb") as f:
        project = pickle.load(f)

    # Update path if file name/path changed
    project.path = project_path

    return project
