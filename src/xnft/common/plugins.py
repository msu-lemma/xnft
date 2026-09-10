"""
Provides plugin discovery for loaders, algorithms, reports, etc.

Discovers plugins registered in namespace packages using a plugins manafest. This module
will read the plugins manifest using the importlib.metadata.EntryPoints listed in the
"xnft.plugins" group in the pyproject.toml for the modules.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


def register_plugins() -> None:
    """Import all installed xNFT plugin modules."""

    for entry_point in entry_points(group="xnft.plugins"):
        logger.debug(
            "Loading plugin %s from %s",
            entry_point.name,
            entry_point.value,
        )
        entry_point.load()
