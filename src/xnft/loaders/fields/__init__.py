"""
Import loaders so that they are added to the registry list.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

# NOTE: automated discovery technique did not work with pyiinstaller packaging so manual imports are used here
from .analytic import *
from .hfss import *
from .lemma import *
from .nsi import *
