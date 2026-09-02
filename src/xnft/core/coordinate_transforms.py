"""
Transformations between coordinate systems.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""
from __future__ import annotations

import numpy as np


# @nb.njit(fastmath=True, cache=True)
def phitheta_to_unit(phi, theta):
    """
    Projection of unit spherical coordinates onto cartesian plane.

    Parameters
    ----------
    phi
        Rotation in radians from the x-axis about the z-axis.
    theta
        Rotation in radians from the z-axis along the phi-z plane.

    Returns
    -------
    np.ndarray
        (ux, uy, uz)
    """
    ux = np.sin(theta) * np.cos(phi)
    uy = np.sin(theta) * np.sin(phi)
    uz = np.cos(theta)
    return ux, uy, uz
