"""
Reporting plot domains available to transform data.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from collections import namedtuple

import numpy as np

logger = logging.getLogger(__name__)

PlotDomain = namedtuple("PlotDomain", ("name", "components", "function"))


def direction_cosine(phi, theta):
    ux = np.sin(theta) * np.cos(phi)
    uy = np.sin(theta) * np.sin(phi)
    uz = np.cos(theta)
    return np.array([ux, uy, uz])


class PlotDomains:
    CARTESIAN = PlotDomain("Cartesian (x,y,z)", ("x", "y", "z"), lambda x: x)
    SPHERICAL = PlotDomain("Spherical (r,θ,φ)", ("r", "theta", "phi"), lambda x: x)

    DIRECTION_COSINE_XY = PlotDomain(
        "Direction Cosine (Ux,Uy)",
        ("Ux", "Uy"),
        lambda phi, theta: direction_cosine(phi, theta)[[0, 1]],
    )
    DIRECTION_COSINE_XZ = PlotDomain(
        "Direction Cosine (Ux,Uz)",
        ("Ux", "Uz"),
        lambda phi, theta: direction_cosine(phi, theta)[[0, 2]],
    )
    DIRECTION_COSINE_YZ = PlotDomain(
        "Direction Cosine (Uy,Uz)",
        ("Uy", "Uz"),
        lambda phi, theta: direction_cosine(phi, theta)[[1, 2]],
    )
