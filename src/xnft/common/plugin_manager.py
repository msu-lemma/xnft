"""
Provides plugin discovery for loaders, algorithms, reports, etc.

Discovers plugins registered in namespace packages using a plugins manafest. This module
will read the plugins manifest using the importlib.metadata.EntryPoints listed in the
"xnft.plugins" group in the pyproject.toml for the modules.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from importlib.metadata import entry_points

from .registry import registry


def discover_plugins():
    for ep in entry_points(group="xnft.plugins"):
        plugin = ep.load()

        registry.loaders.update(plugin.get("loaders", {}))
