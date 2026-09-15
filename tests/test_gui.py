"""
Test GUI components.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from xnft.gui.app import MainWindow
from xnft.project import manager


def test_main_window(qtbot):

    pm = manager.Manager()
    window = MainWindow(pm)

    qtbot.addWidget(window)
