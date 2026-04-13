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
from types import NoneType
import unyt



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
    QDialog,
    QAbstractItemView,
)

from ..enums import CoordinateSystemType
from ...project.nodes.node import DataNode
from ...core.reports.scales import PlotScale
from ...gui.dialogs.reports.new_trace_dialog import NewTraceDialog, TraceParameters
from .plot_helpers import trace_preview


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

        self._abscissa = None
        self._abscissa_units = None

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
        self.pb_edit_trace.setEnabled(False)

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
                self._add_trace(trace=trace)
        else:
            # Initialize data to list of traces
            report_node.data = []

        # ---- Connections ----
        # self.lw_traces.itemSelectionChanged.connect(self._update_plot)
        self.pb_add_trace.clicked.connect(self._add_trace)
        self.pb_remove_trace.clicked.connect(self._remove_trace)

        # Draw initial plot
        self._update_plot()

        # Set layout ratio (for some reason doesn't work if set at creation)
        QTimer.singleShot(0, lambda: layout.setSizes([300, 1000]))

    # def _update_traces(self):
    #     pass

    @property
    def num_traces(self):
        return self.trace_list_widget.topLevelItemCount()

    @property
    def abscissa(self) -> str | None:
        return self._abscissa

    @abscissa.setter
    def abscissa(self, value: str | None):
        if not isinstance(value, (str, NoneType)):
            raise TypeError("Abscissa must be of type string or None.")
        self._abscissa = value
        self._update_abscissa()

    @property
    def abscissa_units(self) -> str | None:
        return self._abscissa_units

    @abscissa_units.setter
    def abscissa_units(self, value: str | None):
        if not isinstance(value, (str, NoneType)):
            raise TypeError("Abscissa units must be of type string or None.")
        self._abscissa_units = value
        self._update_abscissa()

    def _update_abscissa(self):
        abscissa_name = self.abscissa.title() if isinstance(self.abscissa, str) else None
        abscissa_units = self.abscissa_units if isinstance(self.abscissa_units, str) else None
        self.plot.setLabel("bottom", text=abscissa_name, units=abscissa_units)

    def _update_ordinate(self):
        # TODO: Create helper function to manage this outside of _add_trace()
        pass

    def _update_plot(self):
        pass

    def _add_trace(self, clicked: bool = False, trace: PlotTrace | None = None):
        """Add a trace object to ReportNode to hold plot state."""

        trace_list = []
        if trace is None:
            dialog = NewTraceDialog(parent=self, project_node=self.report_node.root)
            if dialog.exec() == QDialog.Accepted:
                trace_parameters_list = dialog.get_selections()

                for tp in trace_parameters_list:
                    # Generate the PlotTrace from the provided arguments

                    # -- Abscissa --
                    if tp.source_field.data is not None:
                        source_field = tp.source_field.data["E"]
                    else:
                        raise RuntimeError("Source field data is not populated.")

                    abscissa_values = source_field[tp.abscissa]
                    abscissa_units = tp.source_field.data.attrs["coordinate_units"][tp.abscissa]
                    if abscissa_units == unyt.radian:
                        abscissa_values = np.rad2deg(abscissa_values)

                    # -- Ordinate --
                    ordinate_raw_values = source_field.sel(**tp.slice_dict)
                    ordinate_values = tp.ordinate_scale.function(
                        tp.ordinate_function.function(tp.field_norm.function(ordinate_raw_values))
                    )

                    ordinate_units = tp.ordinate_scale.unit_modifier(
                        tp.field_norm.unit_modifier(tp.field_quantity.units)
                    )

                    ordinate_name = tp.field_quantity.name

                    # Update ordinate name if a function is applied
                    if tp.ordinate_function is not None:
                        ordinate_name = f"{tp.ordinate_function.name_short}({ordinate_name})"

                    # -- Trace ---
                    trace = PlotTrace(
                        # -- PlotDataItem Parameters --
                        x=abscissa_values,
                        y=ordinate_values,
                        name=tp.trace_name,
                        pen=tp.trace_pen,
                        symbol=tp.trace_marker_symbol,
                        symbolBrush=pg.mkBrush(tp.trace_pen.color()),
                        symbolPen=None,
                        # -- Added PlotTrace Parameters --
                        source=tp.source_field,
                        trace_parameters=tp,
                        ordinate_name=ordinate_name,
                        ordinate_scale=tp.ordinate_scale,
                        ordinate_units=ordinate_units,
                    )
                    trace_list.append(trace)
        else:
            trace_list.append(trace)

        for trace in trace_list:
            # Must add trace to plot before widget to generate trace icon properly for legend
            self.plot.addItem(trace)
            self.trace_list_widget.add_trace(trace)

            # Set Abscissa units
            tp = trace.trace_parameters
            self.abscissa = tp.abscissa
            abscissa_units = tp.source_field.data.attrs["coordinate_units"][tp.abscissa]

            if abscissa_units == unyt.radian:
                abscissa_units = str(unyt.degree)

            self.abscissa_units = str(abscissa_units)

            # Set ordiante units
            # self._update_ordinate()
            ordinate_name = trace.ordinate_name
            ordinate_units = str(trace.ordinate_units)
            self.plot.setLabel("left", text=ordinate_name, units=ordinate_units)

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

            # Clear abscisa if no traces left
            if self.num_traces == 0:
                self.abscissa = None
                self.abscissa_units = None

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

        # Set editable enabled
        self.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
        )

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

        item.setFlags(item.flags() | Qt.ItemIsEditable)

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
        # screen = trace.scene().views()[0].screen()
        # dpr = screen.devicePixelRatio() if screen else 1.0

        # pixmap = QPixmap(int(width * dpr), int(height * dpr))
        # pixmap.setDevicePixelRatio(dpr)

        pixmap = trace_preview(
            pen=trace.curve.opts['pen'],
            symbol=trace.opts['symbol'],
            symbol_brush=trace.opts['symbolBrush'],
            symbol_pen=trace.opts['symbolPen'],
            symbol_size=trace.opts['symbolSize'],
            background=Qt.black,
        )

        label = QLabel()
        label.setPixmap(pixmap)
        label.setContentsMargins(0, 0, 0, 0)
        return label

    def _update_traces(self, item, column):
        # Name column (allow user to update trace name)
        if column == 0:
            # Guard against updates before trace is fully populated
            trace = item.data(0, Qt.UserRole)
            if trace is not None:
                x, y = trace.getData()
                trace.setData(x=x, y=y, name=item.text(0))

        # Trace enabled column
        if column == 2:
            enabled = item.checkState(2) == Qt.Checked
            item.data(0, Qt.UserRole).setVisible(enabled)


class PlotTrace(pg.PlotDataItem):
    def __init__(
        self,
        source: DataNode,
        trace_parameters: TraceParameters,
        ordinate_name: str,
        ordinate_units: str,
        ordinate_scale: PlotScale,
        *args,
        **kwargs,
    ):
        """
        Helper subclass of PlotDataItem to store source data and slice information for traces.

        All kwargs are passed to PyQtGraph PlotDataItem.

        source : DataNode
            Node containing data to plot
        trace_parameters : TraceParameters
            Dictionary containing trace args supplied by user (via helper dialog)
        ordinate_name : str
            String to display on the ordinate axis
        ordinate_units : unyt.unit
            Units to display on the axis
        ordinate_scale : PlotScale
            Scaleing to use for plot (e.g., dB, linear, etc.)
        """
        super().__init__(*args, **kwargs)

        self.source = source
        self.trace_parameters = trace_parameters
        self.ordinate_name = ordinate_name
        self.ordinate_units = ordinate_units
        self.ordinate_scale = ordinate_scale
