"""Module providing graphical user interfaces."""

import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
)

from . import __version__


class MainWindow(QWidget):
    """
    Main Qt window object.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"xnft - version {__version__}")

        layout = QVBoxLayout(self)

        # Input widgets
        self.button = QPushButton("Update PLot")
        self.button.clicked.connect(self.update_plot)

        # PyQtGraph plot widget
        self.plot = pg.PlotWidget(title="Example Plot")
        self.plot.showGrid(x=True, y=True)

        # Add widgets to layout
        layout.addWidget(self.button)
        layout.addWidget(self.plot)

        # Initial plot
        self.x = np.linspace(0, 2 * np.pi, 100)
        self.y = np.sin(self.x)
        self.curve = self.plot.plot(self.x, self.y, pen="y")

    def update_plot(self):
        """
        Update plot dynamically.

        For demo use only.
        """
        self.y = np.sin(self.x + np.random.rand() * np.pi)
        self.curve.setData(self.x, self.y)


def main():
    """
    Main GUI entrypoint.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
