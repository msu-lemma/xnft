"""
Import builtin loaders.

Copyright 2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import importlib

_BUILTIN_LOADERS = (
    "xnft.loaders.fields.analytic",
    "xnft.loaders.fields.hfss",
    "xnft.loaders.fields.lemma",
    "xnft.loaders.fields.nsi",
)


def register_builtin_loaders():
    """
    Import builin loader modules to registry.
    """
    for mod in _BUILTIN_LOADERS:
        importlib.import_module(mod)
