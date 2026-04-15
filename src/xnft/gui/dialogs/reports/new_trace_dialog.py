"""
Define new trace dialog window (for dd plots).

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

from quantiphy import Quantity
import numpy as np
from numpy.typing import ArrayLike
import pyqtgraph as pg
import unyt
import platform
import colorcet as cc

from itertools import product

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPixmap, QPainter, QPen, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QWidget,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QLabel,
    QColorDialog,
    QSpinBox,
    QPushButton,
    QMessageBox,
)

from dataclasses import dataclass, field, InitVar
from uuid import uuid4, UUID
from typing import List, Optional, Callable, Any
from numpy.typing import ArrayLike

from ..common import ListWidgetTitle

from ....core.enums import NodeType
from ....project.nodes.node import Node, DataNode
from ....core.reports.normalizations import PlotNorms, PlotNorm
from ....core.reports.field_components import FieldComponent
from ....core.reports.field_quantities import FieldQuantities, FieldQuantity
from ....core.reports.functions import PlotFunction
from ....core.reports.scales import PlotScale
from ....core.reports.plot_helpers import trace_preview


@dataclass
class TraceParameters:
    trace_name: str
    trace_pen: QPen
    trace_marker_symbol: str
    source_field: DataNode
    abscissa: str
    slice_dict: dict[str, ArrayLike]
    field_quantity: FieldQuantity
    field_component: FieldComponent
    ordinate_function: PlotFunction
    ordinate_scale: PlotScale
    field_norm: PlotNorm


class NewTraceDialog(QDialog):
    """
    Input dialog for new trace (line plot).

    Parameters
    ----------
    parent : QWidget | None, optional
        Parent widget for dialog, by default None
    """

    def __init__(self, parent: QWidget, project_node: Node | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Trace")
        self.setMinimumWidth(480)
        self.resize(720, 800)

        self.parent = parent
        self.project_node = project_node

        # ===== Widgets =====

        # -- Trace name section --

        trace_name = QGroupBox()

        trace_name.setFlat(True)
        self.le_trace_name = QLineEdit(self)
        self.le_trace_name.setPlaceholderText("Enter a trace name")

        # Generate default trace name based on number of traces in plot
        num_traces = parent.num_traces
        self.le_trace_name.setText(f"Trace {num_traces + 1}")

        form_layout_trace_name = QFormLayout()
        form_layout_trace_name.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout_trace_name.addRow("Trace Name", self.le_trace_name)
        form_layout_trace_name.setContentsMargins(0, 0, 0, 0)

        trace_name.setLayout(form_layout_trace_name)

        # -- Trace Style --

        self.trace_style = TraceStyleGroupBox()

        # -- Source Field --

        layout_source_selection = QHBoxLayout()
        # form_layout_data.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        group_source_field = QGroupBox("Source Data")
        group_source_field.setLayout(layout_source_selection)

        self.lwt_source_field = ListWidgetTitle("Source Field")
        self.lwt_abscissa = ListWidgetTitle("Abscissa")

        self._update_field_options()

        layout_source_selection.addWidget(self.lwt_source_field)
        layout_source_selection.addWidget(self.lwt_abscissa)

        # -- Data Slicing --

        # NOTE: Data slicing requires one box per axis of data required to slice to achieve a 1D plot
        # e.g., if axes are x, y, z, f; three boxes would be required to slice.

        self.layout_slice_outer = QVBoxLayout()
        self.layout_slice = QHBoxLayout()
        group_slice = QGroupBox("Slice Parameters")

        # Create a dictionary to hold QListWidgets for slices (updated dynamically)
        # [slice_axis_name: ListWidgetTitle]
        self.lwt_slice_dict: dict[str, ListWidgetTitle] = dict()

        # Generate help label based on platform type
        mod_key = "⌘" if platform.system() == "Darwin" else "ctrl"
        self.label_slice_help = QLabel(
            f"To select multiple slice parameters hold {mod_key} or shift, or {mod_key}-A to select all.  Multiple traces will be generated from the product of all column selections; trace style will be automatically cycled (user style will be ignored)."
        )
        self.label_slice_help.setWordWrap(True)
        self.label_slice_help.setStyleSheet("color: #777")

        self.layout_slice_outer.addLayout(self.layout_slice)
        self.layout_slice_outer.addWidget(self.label_slice_help)
        group_slice.setLayout(self.layout_slice_outer)

        # -- Ordinate --
        ordinate_layout = QHBoxLayout()
        group_ordinate = QGroupBox("Ordinate Parameters")
        group_ordinate.setLayout(ordinate_layout)

        self.lwt_field_component = ListWidgetTitle("Field Component")
        self.lwt_field_quantity = ListWidgetTitle("Field Quantity")
        self.lwt_ordinate_function = ListWidgetTitle("Function")
        self.lwt_ordinate_scale = ListWidgetTitle("Scale")
        self.lwt_field_norm = ListWidgetTitle("Normalization")

        ordinate_layout.addWidget(self.lwt_field_quantity)
        ordinate_layout.addWidget(self.lwt_field_component)
        ordinate_layout.addWidget(self.lwt_ordinate_function)
        ordinate_layout.addWidget(self.lwt_ordinate_scale)
        ordinate_layout.addWidget(self.lwt_field_norm)

        # -- Dialog Butons --

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # === Top-level layout ===
        layout = QVBoxLayout(self)

        layout.addWidget(trace_name)
        layout.addWidget(self.trace_style)
        layout.addWidget(group_source_field)
        layout.addWidget(group_slice)
        layout.addWidget(group_ordinate)

        layout.addWidget(self.buttons)

        # === Connections ===
        self.lwt_source_field.lw.itemSelectionChanged.connect(self._update_abscissa_options)
        self.lwt_abscissa.lw.itemSelectionChanged.connect(self._update_slice_options)
        self.lwt_source_field.lw.itemSelectionChanged.connect(self._update_field_quantities)
        self.lwt_field_quantity.lw.itemSelectionChanged.connect(self._update_field_components)
        self.lwt_field_component.lw.itemSelectionChanged.connect(self._update_ordinate_functions)
        self.lwt_ordinate_function.lw.itemSelectionChanged.connect(self._update_ordinate_scales)
        self.lwt_ordinate_scale.lw.itemSelectionChanged.connect(self._update_field_norms)

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)
        self.le_trace_name.returnPressed.connect(self._try_accept)

        # # -- Set current selection row to trigger callbacks --
        self.lwt_source_field.lw.setCurrentRow(0)
        self.lwt_abscissa.lw.setCurrentRow(0)

    # --- Properties ---

    @property
    def selected_field(self):
        return self._get_lwt_selected_item(self.lwt_source_field)

    @property
    def selected_abscissa(self):
        return self._get_lwt_selected_item(self.lwt_abscissa)

    @property
    def selected_field_quantity(self):
        return self._get_lwt_selected_item(self.lwt_field_quantity)

    @property
    def selected_field_component(self):
        return self._get_lwt_selected_item(self.lwt_field_component)

    @property
    def selected_field_function(self):
        return self._get_lwt_selected_item(self.lwt_ordinate_function)

    @property
    def selected_field_scale(self):
        return self._get_lwt_selected_item(self.lwt_ordinate_scale)

    @property
    def selected_field_norm(self):
        return self._get_lwt_selected_item(self.lwt_field_norm)

    # --- Public Methods ---
    def get_selections(self) -> list[TraceParameters]:
        """
        Return values chosen by the user.

        If multiple slices are chosen, list will have multiple dictionaries, one for each trace.
        In this case, the line style should be automatically cycled for convenience.
        """
        output_list: list[TraceParameters] = []

        # Compute products of slice options selected
        slice_list: list[list[tuple[str, float]]] = []
        for axis_name, lwt in self.lwt_slice_dict.items():
            axis_slice_list: list[tuple[str, float]] = []
            for item in lwt.lw.selectedItems():
                axis_slice_list.append((axis_name, item.data(Qt.UserRole)))
            slice_list.append(axis_slice_list)
        slice_list_products = list(product(*slice_list))

        for idx, slice_list_idx in enumerate(slice_list_products):

            # -- Trace name --
            trace_name_suffix = ""
            if len(slice_list_products) != 1:
                trace_name_suffix = f"-{idx+1}"
            trace_name = self.le_trace_name.text().strip() + trace_name_suffix

            # -- Trace Style --
            if len(slice_list_products) == 1:
                trace_pen = self.trace_style.get_pen()
                trace_marker_symbol = self.trace_style.cb_marker_symbol.currentData()
            else:
                trace_pen = pg.mkPen(
                    color=QColor(cc.glasbey_light[idx]),
                    width=1.0,
                    style=Qt.SolidLine,
                )
                trace_marker_symbol = None

            # -- Slice Parameters --
            slice_dict: dict[str, ArrayLike] = {
                axis_name: slice_value for axis_name, slice_value in slice_list_idx
            }

            trace_params = TraceParameters(
                trace_name=trace_name,
                trace_pen=trace_pen,
                trace_marker_symbol=trace_marker_symbol,
                # -- Source Data --
                source_field=self.lwt_source_field.lw.selectedItems()[0].data(Qt.UserRole),
                abscissa=self.lwt_abscissa.lw.selectedItems()[0].data(Qt.UserRole),
                # -- Slice Parameters --
                slice_dict=slice_dict,
                # -- Ordinate Parameters --
                field_quantity=self.lwt_field_quantity.lw.selectedItems()[0].data(Qt.UserRole),
                field_component=self.lwt_field_quantity.lw.selectedItems()[0].data(Qt.UserRole),
                ordinate_function=self.lwt_ordinate_function.lw.selectedItems()[0].data(
                    Qt.UserRole
                ),
                ordinate_scale=self.lwt_ordinate_scale.lw.selectedItems()[0].data(Qt.UserRole),
                field_norm=self.lwt_field_norm.lw.selectedItems()[0].data(Qt.UserRole),
            )

            output_list.append(trace_params)

        return output_list

    # --- Private Methods ---

    def _get_lwt_selected_item(self, lwt):
        result_list = [x.data(Qt.UserRole) for x in lwt.lw.selectedItems()]
        return result_list[0] if result_list else None

    def _update_field_options(self):
        self.lwt_source_field.lw.clear()

        self.fields_node = None
        for tmp_node in self.project_node.children:
            if tmp_node.node_type == NodeType.FIELDS:
                self.fields_node = tmp_node
                break
        assert self.fields_node is not None

        field_options = [
            (f"{x.name}", x)
            for x in self.fields_node.children
            # if x.node_type == self.cb_field_type.currentData()
        ]

        for label, data in field_options:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lwt_source_field.lw.addItem(item)

    def _update_abscissa_options(self):
        self.lwt_abscissa.lw.clear()

        abscissa_options = [
            (f"{x.title()}", x) for x in self.selected_field.data.coords if x != "component"
        ]

        # If plot has an abscissa already selected, only allow that abscissa
        for label, data in abscissa_options:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            if self.parent.abscissa != None and data != self.parent.abscissa:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.lwt_abscissa.lw.addItem(item)

        self.lwt_abscissa.lw.setCurrentRow(0)

    def _update_slice_options(self):
        # Need to create N QListWidget boxes to select slice dimenstions in order to reduce ndims to 1
        slice_keys = [
            x
            for x in self.selected_field.data.coords
            if x != "component" and x != self.selected_abscissa
        ]

        # Remove old list widgets
        for key in list(self.lwt_slice_dict.keys()):
            lwt = self.lwt_slice_dict.pop(key)
            self.layout_slice.removeWidget(lwt)
            lwt.setParent(None)
            lwt.deleteLater()

        # Add new list widgets
        for key in sorted(slice_keys):
            if key not in self.lwt_slice_dict:
                label = key.title()
                lwt = ListWidgetTitle(label)

                # Allow multiple selections
                lwt.lw.setSelectionMode(QListWidget.ExtendedSelection)

                # Add data to list widget
                data = self.selected_field.data[key]
                units = self.selected_field.data.attrs["coordinate_units"][key]
                for value in np.nditer(data):
                    if units == unyt.radian:
                        scale = 180 / np.pi
                        label = f"{round(value * scale, 6)}°"
                    else:
                        label = str(Quantity(value, str(units)))
                    item = QListWidgetItem(label)
                    item.setData(Qt.UserRole, value)
                    lwt.lw.addItem(item)
                    lwt.lw.setCurrentRow(0)

                self.lwt_slice_dict[key] = lwt
                self.layout_slice.addWidget(lwt)

    def _update_field_quantities(self):
        # Remove all items before updating items
        self.lwt_field_quantity.lw.clear()

        field_components = FieldQuantities

        for fc in field_components:
            item = QListWidgetItem(fc.value.name)
            item.setData(Qt.UserRole, fc.value)
            if not fc.value.enabled:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.lwt_field_quantity.lw.addItem(item)

        self.lwt_field_quantity.lw.setCurrentRow(0)

    def _update_field_components(self):
        # Remove all items before updating items
        self.lwt_field_component.lw.clear()

        if self.selected_field_quantity is not None:
            field_components = self.selected_field_quantity.field_components

            for fc in field_components:
                # Only add if field type is valid for that function
                if self.selected_field.data.attrs['field_type'] in fc.value.field_types:
                    item = QListWidgetItem(fc.value.name)
                    item.setData(Qt.UserRole, fc.value)
                    if not fc.value.enabled:
                        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    self.lwt_field_component.lw.addItem(item)

            self.lwt_field_component.lw.setCurrentRow(0)

    def _update_ordinate_functions(self):
        # Remove all items before updating items
        self.lwt_ordinate_function.lw.clear()

        if self.selected_field_component is not None:
            field_functions = self.selected_field_component.plot_functions

            for ff in field_functions:
                item = QListWidgetItem(ff.value.name)
                item.setData(Qt.UserRole, ff.value)
                if not ff.value.enabled:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.lwt_ordinate_function.lw.addItem(item)

            self.lwt_ordinate_function.lw.setCurrentRow(0)

    def _update_ordinate_scales(self):
        # Remove all items before updating items
        self.lwt_ordinate_scale.lw.clear()

        if self.selected_field_function is not None:
            field_scales = self.selected_field_function.scales

            for fs in field_scales:
                item = QListWidgetItem(fs.value.name)
                item.setData(Qt.UserRole, fs.value)
                if not fs.value.enabled:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.lwt_ordinate_scale.lw.addItem(item)

            self.lwt_ordinate_scale.lw.setCurrentRow(0)

    def _update_field_norms(self):
        # Remove all items before updating items
        self.lwt_field_norm.lw.clear()

        if self.selected_field_scale is not None:
            field_norms = [x for x in PlotNorms]

            for fn in field_norms:
                item = QListWidgetItem(fn.value.name)
                item.setData(Qt.UserRole, fn.value)
                if not fn.value.enabled:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.lwt_field_norm.lw.addItem(item)

            self.lwt_field_norm.lw.setCurrentRow(0)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_trace_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(self, "Missing Name", "Please enter a transform node name.")
            return False

        lwt_fields = [
            self.lwt_source_field,
            self.lwt_abscissa,
            self.lwt_field_quantity,
            self.lwt_field_component,
            self.lwt_ordinate_function,
            self.lwt_ordinate_scale,
            self.lwt_field_norm,
        ]

        for lwt in lwt_fields:
            if not lwt.lw.selectedItems():
                if not silent:
                    QMessageBox.warning(
                        self,
                        "Missing Field(s)",
                        f"Please select {lwt.name.lower()} for the report.",
                    )
                return False

        # Check slices dict for selections
        for name, lwt in self.lwt_slice_dict.items():
            if not lwt.lw.selectedItems():
                if not silent:
                    QMessageBox.warning(
                        self,
                        "Missing Field(s)",
                        f"Please select {name.lower()} slice for the report.",
                    )
                return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()


class TraceStyleGroupBox(QGroupBox):
    def __init__(self, title="Trace Style", parent=None):
        super().__init__(title, parent)

        self.current_color = QColor("#ffffff")

        layout = QHBoxLayout(self)
        layout.setSpacing(24)

        # -- Color --
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(32, 20)
        self._update_color_button()
        self.color_btn.clicked.connect(self.pick_color)

        layout.addLayout(self._labeled_control("Color", self.color_btn))

        # -- Line Style --
        self.cb_line_style = QComboBox()
        self.line_styles = {
            "Solid": Qt.SolidLine,
            "Dash": Qt.DashLine,
            "Dot": Qt.DotLine,
            "Dash Dot": Qt.DashDotLine,
            "Dash Dot Dot": Qt.DashDotDotLine,
        }
        self.cb_line_style.clear()
        for name, style in self.line_styles.items():
            icon = trace_preview(
                pen=QPen(Qt.black, 2, style),
                background=Qt.transparent,
                width=30,
                height=20,
            )
            self.cb_line_style.addItem(icon, name)
            self.cb_line_style.setItemData(self.cb_line_style.count() - 1, style, Qt.UserRole)

        layout.addLayout(self._labeled_control("Line Style", self.cb_line_style))

        # -- Line Width --
        self.sb_line_width = QSpinBox()
        self.sb_line_width.setRange(1, 10)
        self.sb_line_width.setValue(1)
        layout.addLayout(self._labeled_control("Width", self.sb_line_width))

        # -- marker_symbol --
        self.cb_marker_symbol = QComboBox()
        self.marker_symbol_map = {
            "None": None,
            "Circle": "o",
            "Square": "s",
            "Triangle": "t",
            "Diamond": "d",
            "Plus": "+",
            "X": "x",
        }
        self.cb_marker_symbol.addItems(self.marker_symbol_map.keys())
        self.cb_marker_symbol.clear()
        for name, symbol in self.marker_symbol_map.items():
            icon = trace_preview(
                pen=None,
                symbol=symbol,
                symbol_brush=pg.mkBrush(QColor("black")),
                symbol_pen=None,
                symbol_size=10,
                background=Qt.transparent,
                width=20,
                height=20,
            )
            self.cb_marker_symbol.addItem(icon, name)
            self.cb_marker_symbol.setItemData(
                self.cb_marker_symbol.count() - 1, symbol, Qt.UserRole
            )
        layout.addLayout(self._labeled_control("marker_symbol", self.cb_marker_symbol))

        # -- Final Trace Preview --
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(48, 16)
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addLayout(self._labeled_control("Preview", self.preview_label))

        self._update_preview()

        self.cb_line_style.currentIndexChanged.connect(lambda _: self._update_preview())
        self.sb_line_width.valueChanged.connect(lambda _: self._update_preview())
        self.cb_marker_symbol.currentIndexChanged.connect(lambda _: self._update_preview())

        layout.addStretch()

    def pick_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self._update_color_button()
            self._update_preview()

    def get_pen(self):
        """Create pen for pyqgraph plot."""
        pen = pg.mkPen(
            color=self.current_color,
            width=self.sb_line_width.value(),
            style=self.line_styles[self.cb_line_style.currentText()],
        )
        return pen

    def _labeled_control(self, text, widget):
        """Create label above control."""
        layout = QVBoxLayout()
        layout.setSpacing(4)

        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setFixedHeight(16)

        layout.addWidget(label)
        layout.addWidget(widget, alignment=Qt.AlignHCenter | Qt.AlignVCenter)

        layout.setStretch(0, 0)  # label
        layout.setStretch(1, 1)  # control takes available space

        return layout

    def _update_color_button(self):
        """Update color of color selection button."""
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #666;
            }}
            """)

    def _update_preview(self, width=40, height=20):
        """Light wrapper on trace_preview to update preview for menu.

        Parameters
        ----------
        width : int, optional
            Width of trace preview, by default 40
        height : int, optional
            Height of trace preview, by default 20
        """
        pixmap = trace_preview(
            pen=self.get_pen(),
            symbol=self.marker_symbol_map[self.cb_marker_symbol.currentText()],
            symbol_brush=pg.mkBrush(self.current_color),
            symbol_pen=None,
            symbol_size=10,
            background=Qt.black,
            width=width,
            height=height,
        )

        self.preview_label.setPixmap(pixmap)

    @staticmethod
    def _make_line_style_icon(style, color=QColor("black")):
        """Generate QListWidget line style preview icon."""
        pm = QPixmap(40, 14)
        pm.fill(Qt.transparent)

        painter = QPainter(pm)
        pen = QPen(color, 2, style)
        painter.setPen(pen)

        y = pm.height() // 2
        painter.drawLine(2, y, pm.width() - 2, y)
        painter.end()

        return pm
