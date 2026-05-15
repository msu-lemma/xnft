"""
Module providing GUI utility functions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from PySide6.QtGui import QWindow


def center_window(window: QWindow, target_size_ratio: float = 0.7):
    """Center and resize the window to fill a fraction of the display.

    Parameters
    ----------
    window : QWindow
        Window to be resized
    target_size_ratio : float, optional
        Fraction of the display to resize the window to, by default 0.7
    """
    min_width = 768  # px
    min_height = 576  # px

    # Get window geometry
    screen = window.screen()

    # If the screen is available proceed with resizing
    if screen:
        available_geometry = screen.availableGeometry()

        # Set to xx% or min size, whichever is larger
        target_size_ratio = 0.7
        target_width = int(available_geometry.width() * target_size_ratio)
        target_height = int(available_geometry.height() * target_size_ratio)

        width = max(target_width, min_width)
        height = max(target_height, min_height)

        window.resize(width, height)

        # Center the window
        x = available_geometry.x() + (available_geometry.width() - width) // 2
        y = available_geometry.y() + (available_geometry.height() - height) // 2

        window.move(x, y)

        window.setMinimumWidth(min_width)
        window.setMinimumHeight(min_height)
