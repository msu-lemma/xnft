"""
Handle xnft 1d plotting actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.

TODO: Add colormap selection (based on type of scale user selected)
TODO: Add plot normalization
    - Source units (unnormalized)
    - Relative to local maxima (simply the peak value)
    - Relative to global maxima (across all frequencies)
"""

import logging
import numpy as np
import pyqtgraph as pg
import xarray as xr

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QSizePolicy,
    QComboBox,
    QFormLayout,
    QPushButton,
    QLabel,
    QDialog
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor

from ..enums import CoordinateSystemType

from .functions import PlotFunctions
from .scales import PlotScales
from ..coordinate_transforms import phitheta_to_unit

from quantiphy import Quantity

from ...gui.dialogs.reports.new_trace_dialog import NewTraceDialog

logger = logging.getLogger(__name__)

# TODO: this should be moved elsewhere
pg.setConfigOption("useNumba", True)


class Plot1D(QWidget):
    # Mapping of valid source coordinates to plotting coordinates
    __coordinate_domains__ = {
        CoordinateSystemType.SPHERICAL: (
            CoordinateSystemType.SPHERICAL,
            CoordinateSystemType.DIRECTION_COSINE,
            # CoordinateSystemType.SPHERICAL_AZEL,
        ),
        CoordinateSystemType.CARTESIAN: (CoordinateSystemType.CARTESIAN,),
    }

    def __init__(
        self,
        report_node,
        coordinates_type=CoordinateSystemType.SPHERICAL,
        parent=None,
    ):
        """
        Parameters
        ----------
        field : xr.Dataset
            Far field dataset containing E and H fields and respective
            components.
        coordinates_type : str
            Coordinate system type to plot in.
        """
        super().__init__(parent)

        self.report_node = report_node

        if coordinates_type not in self.__coordinate_domains__.keys():
            raise ValueError(
                f"Plot coordinates must be one of {[x.name for x in self.__coordinate_domains__.keys()]},"
                f" got {coordinates_type.name}"
            )

        self.abscissa = None
        self.trace_list = []

        # === Update Plotting Options ===

        # self._update_traces()
        # self.trace_list_widget.setCurrentRow(0)

        # === Add 2D Field View ===
        self.glw = pg.GraphicsLayoutWidget()
        self.plot = self.glw.addPlot()
        self.vb = self.plot.getViewBox()

        # === Add control widgets ===

        layout_controls = QVBoxLayout()
        layout_controls.setContentsMargins(0, 0, 0, 0)
        layout_controls.setSpacing(4)

        # -- Add Trace List --
        self.trace_list_widget = TraceList(self.plot)
        self.trace_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add +/-, edit buttons
        self.pb_add_trace = QPushButton("+")
        self.pb_remove_trace = QPushButton("-")
        self.pb_edit_trace = QPushButton("Edit")

        layout_controls.addWidget(QLabel("Traces"))
        layout_controls.addWidget(self.trace_list_widget)

        # Add Layout row for buttons
        button_row = QHBoxLayout()
        button_row.addWidget(self.pb_add_trace)
        button_row.addWidget(self.pb_remove_trace)
        button_row.addWidget(self.pb_edit_trace)
        layout_controls.addLayout(button_row)

        # === Main Layout ===
        plot_layout = QVBoxLayout(self)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.glw)

        # Add split layout for frequency and plot
        layout = QSplitter(Qt.Orientation.Horizontal)

        layout_controls_widget = QWidget()
        layout_controls_widget.setLayout(layout_controls)
        layout_controls_widget.setMinimumWidth(150)
        layout.addWidget(layout_controls_widget)

        layout_plot_widget = QWidget()
        layout_plot_widget.setLayout(plot_layout)
        layout_plot_widget.setMinimumWidth(150)
        layout.addWidget(layout_plot_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(layout)

        # Populate trace list with traces from ReportNode
        if report_node.data is not None:
            for trace in self.report_node.data:
                self._add_trace(trace)
        else:
            # Initialize data to list of traces
            report_node.data = []

        # ---- Connections ----
        #self.lw_traces.itemSelectionChanged.connect(self._update_plot)
        self.pb_add_trace.clicked.connect(self._add_trace)
        self.pb_remove_trace.clicked.connect(self._remove_trace)
        
        # Draw initial plot
        self._update_plot()

        # Set layout ratio (for some reason doesn't work if set at creation)
        QTimer.singleShot(0, lambda: layout.setSizes([300, 1000]))

    # def _update_traces(self):
    #     pass

    def _update_plot(self):
        pass

    def _add_trace(self):
        """Add a trace object to ReportNode to hold plot state."""
        dialog = NewTraceDialog(parent=self, project_node=self.report_node.root)
        if dialog.exec() == QDialog.Accepted:
            trace = dialog.get_selections()

            # Must add trace to plot before widget to generate trace icon properly for legend
            self.plot.addItem(trace)
            self.trace_list_widget.add_trace(trace)

            if trace not in self.report_node.data:
                self.report_node.data.append(trace)

    def _remove_trace(self):
        # Get selected trace from tree
        selected_trace_list = self.trace_list_widget.selectedItems()

        # Exactly zero or one should be selected
        if len(selected_trace_list) == 1:
            trace_item = selected_trace_list[0]
            trace_index = self.trace_list_widget.indexFromItem(trace_item).row()
            trace = trace_item.data(0, Qt.UserRole)

            # Must add trace to plot before widget to generate trace icon properly for legend
            self.plot.removeItem(trace)
            self.trace_list_widget.remove_trace(trace_index)

            if trace in self.report_node.data:
                self.report_node.data.remove(trace)

    def _edit_trace(self):
        pass

    def _update_coordinate_system_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_coordinate_system.count()):
            self.cb_coordinate_system.removeItem(0)

        pass

    def _update_abscissa_options(self):
        pass

class TraceList(QTreeWidget):
    def __init__(self, plot):
        super().__init__()
        
        self.plot = plot

        self.setColumnCount(3)
        self.setHeaderLabels(["Name", "Trace", "Show"])
        self.setRootIsDecorated(False)  # Remove indentation for icon
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)

        self.itemChanged.connect(self._update_traces)


    def add_trace(self, trace):
        """Add trace to list.

        Parameters
        ----------
        trace : PlotTrace
            Trace object to add to trace list.
        enabled : bool, optional
            Whether the trace is shown or not, by default True
        """
        
        item = QTreeWidgetItem(self)
        item.setText(0, trace.name())
        item.setData(0, Qt.UserRole, trace)

        # # Checkbox column
        item.setCheckState(2, Qt.Checked if trace.isVisible() else Qt.Unchecked)

        # Trace preview
        preview = self._get_trace_icon(trace)
        self.setItemWidget(item, 1, preview)

        # Columns can only be properly resized once data exists in columns
        self.resizeColumnToContents(1)
        self.resizeColumnToContents(2)

    def remove_trace(self, trace_index):
        """Remove trace from trace list.

        Parameters
        ----------
        trace_index : int
            Integer index of row to remove.
        """
        self.takeTopLevelItem(trace_index)

    def _get_trace_icon(self, trace: PlotTrace, width=40, height=20):
        """Generate trace icon to display in trace list widget.

        Parameters
        ----------
        trace : PlotTrace
            Trace to display
        width : int, optional
            Width of the trace icon to draw, by default 40
        height : int, optional
            Height of the trace icon to draw, by default 20

        Returns
        -------
        QLabel
            QLabel containing the Pixmap to show in the table widget
        """
        # Get screen dpi to render image properly
        screen = trace.scene().views()[0].screen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        pixmap = QPixmap(int(width * dpr), int(height * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)

        pen = trace.opts.get('pen', None)
        if pen is not None:
            pen = pg.mkPen(pen)
            pen.setCosmetic(True)
            painter.setPen(pen)
            y = height // 2
            painter.drawLine(4, y, width - 4, y)

        symbol = trace.opts.get('symbol', None)
        if symbol:
            symbol_pen = pg.mkPen(trace.opts.get('symbolPen'))
            symbol_brush = pg.mkBrush(trace.opts.get('symbolBrush'))
            size = trace.opts.get('symbolSize', 10)

            painter.setPen(symbol_pen)
            painter.setBrush(symbol_brush)

            center_x = width // 2
            center_y = height // 2
            pg.functions.drawSymbol(
                painter,
                symbol,
                center_x,
                center_y,
                size=size
            )

        painter.end()

        label = QLabel()
        label.setPixmap(pixmap)
        label.setContentsMargins(0, 0, 0, 0)
        return label
    
    def _update_traces(self, item, column):
        if column == 2:
            enabled = item.checkState(2) == Qt.Checked
            item.data(0, Qt.UserRole).setVisible(enabled)


class PlotTrace(pg.PlotDataItem):
    def __init__(self, source, visible=True, *args, **kwargs):
        """
        Helper subclass of PlotDataItem to store source data and slice information for traces.

        All kwargs are passed to PyQtGraph PlotDataItem.
        
        source : DataNode
            Node containing data to plot
        visible : bool
            Flag to enable/disable trace rendering, by default True
        """
        super().__init__(*args, **kwargs)

        self.source = source
