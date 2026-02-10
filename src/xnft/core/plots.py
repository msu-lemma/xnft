"""
Handle xnft plotting actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QSplitter,
    QGroupBox,
    QSizePolicy,
)


from quantiphy import Quantity

logger = logging.getLogger(__name__)


class Plot2D(QWidget):

    def __init__(self, field, parent=None):
        """
        Parameters
        ----------
        field : xr.Dataset
            Far field dataset containing E and H fields and respective
            components.
        """
        super().__init__(parent)

        self.field = field

        # -- Add Frequency Selection --
        self.lw_frequency_range = QListWidget()
        self.lw_frequency_range.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self._update_frequency_options()
        self.lw_frequency_range.setCurrentRow(0)
        self.lw_frequency_range.setMinimumWidth(100)

        self.frequency_selection = QGroupBox("Frequency", parent=self)
        box_layout = QVBoxLayout()
        box_layout.addWidget(self.lw_frequency_range, 1)
        box_layout.setContentsMargins(5, 5, 5, 5)
        box_layout.setSpacing(0)
        self.frequency_selection.setLayout(box_layout)

        # -- Add 2D Field View --
        self.field_view = pg.GraphicsLayoutWidget()
        plot = self.field_view.addPlot()
        self.field_view.addItem(plot, 0, 0, 1, 1)
        # self.img = pg.ImageItem()
        # plot.addItem(self.img)

        # Create autoscaling image item
        edgecolors = None
        antialiasing = False
        cmap = pg.colormap.get("viridis")
        levels = (
            -2,
            2,
        )  # Will be overwritten unless enableAutoLevels is set to False
        self.img = pg.PColorMeshItem(
            edgecolors=edgecolors,
            antialiasing=antialiasing,
            colorMap=cmap,
            levels=levels,
            enableAutoLevels=True,
        )
        self.theta_grid, self.phi_grid = np.meshgrid(
            self.field.data.theta, self.field.data.phi
        )
        plot.addItem(self.img)

        # hist = pg.HistogramLUTItem()
        # hist.setImageItem(self.img)
        # self.field_view.addItem(hist)

        # Add colorbar
        bar = pg.ColorBarItem(
            label="Z value [arbitrary unit]",
            interactive=True,
            rounding=0.1,
        )
        bar.setImageItem([self.img])
        self.field_view.addItem(bar, 0, 1, 1, 1)

        # Add split layout for frequency and plot
        self.layout = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.frequency_selection)
        self.layout.addWidget(self.field_view)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.layout)

        # ---- Connections ----
        self.lw_frequency_range.itemSelectionChanged.connect(self._update_plot)

        # Draw initial plot
        self._update_plot()

        QTimer.singleShot(0, lambda: self.layout.setSizes([100, 1000]))

    def _update_frequency_options(self):
        # Remove all items before updating items
        self.lw_frequency_range.clear()

        frequencies = self.field.data.coords["frequency"].values.tolist()

        # Get only unique items
        frequencies = list(set(frequencies))

        frequencies_items = sorted(
            [(str(Quantity(x, units="Hz")), x) for x in frequencies]
        )
        for label, data in frequencies_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_frequency_range.addItem(item)

    def _update_plot(self):
        selected_frequency_list = self.lw_frequency_range.selectedItems()
        selected_frequency = [
            x.data(Qt.UserRole) for x in selected_frequency_list
        ]

        field_data = self.field.data.sel(
            frequency=selected_frequency,
        )

        e_mag = np.linalg.norm(np.abs(field_data["E"]), ord=2, axis=0)
        # self.img.setImage(10 * np.log10(e_mag))

        self.img.setData(self.phi_grid, self.theta_grid, 10 * np.log10(e_mag))
