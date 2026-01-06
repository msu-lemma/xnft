"""
Automatically discover and import modules in loaders.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

import importlib
import pkgutil

for module_info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_info.name}")
