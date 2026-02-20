"""
Automatically discover and import modules in loaders.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import importlib
import pkgutil

path = [__path__[0] + '/loaders']
for module_info in pkgutil.iter_modules(path):
    importlib.import_module(f"{__name__}.loaders.{module_info.name}")
