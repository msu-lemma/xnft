"""
Helper functions for reports.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import pyqtgraph as pg
from pyqtgraph.graphicsItems.ScatterPlotItem import drawSymbol
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap


def trace_preview(
    pen,
    symbol=None,
    symbol_brush=None,
    symbol_pen=None,
    symbol_size=10,
    background=Qt.transparent,
    width=40,
    height=20,
):
    """
    Generate trace preview pixmap.

    Parameters
    ----------
    width : int, optional
        Width of the trace pixmap to draw, by default 40
    height : int, optional
        Height of the trace pixmap to draw, by default 20

    Returns
    -------
    QPixmap
        QPixmap render of plot trace
    """
    pixmap = QPixmap(int(width), int(height))
    pixmap.fill(background)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, False)

    if pen is not None:
        pen = pg.mkPen(pen)
        pen.setCosmetic(True)
        painter.setPen(pen)
        y = height // 2
        painter.drawLine(4, y, width - 4, y)

    if symbol:
        center_x = width // 2
        center_y = height // 2

        painter.save()
        painter.translate(center_x, center_y)

        drawSymbol(
            painter=painter,
            symbol=symbol,
            size=symbol_size,
            pen=symbol_pen if symbol_pen is not None else Qt.NoPen,
            brush=symbol_brush,
        )

        painter.restore()

    painter.end()

    return pixmap
