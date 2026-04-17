"""
Automatically discover and import modules in loaders.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

# Manually import each module to add it to the registry
from .loaders.hfss import *
from .loaders.lemma import *
from .loaders.theory import *
