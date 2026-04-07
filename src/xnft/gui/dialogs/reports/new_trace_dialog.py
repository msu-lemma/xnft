"""
Define new trace dialog window (for dd plots).

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

from quantiphy import Quantity

import numpy as np
import platform
import pyqtgraph as pg
import unyt

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
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QLabel,
    QColorDialog,
    QSpinBox,
    QPushButton, 
)

from ....core.enums import NodeType
from ....project.nodes.node import Node


class NewTraceDialog(QDialog):
    """
    Input dialog for new trace (line plot).

    Parameters
    ----------
    parent : QWidget | None, optional
        Parent widget for dialog, by default None
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        project_node: Node = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Trace")
        self.setMinimumWidth(480)
        self.resize(640,800)

        self.parent = parent
        self.project_node = project_node

        # ===== Widgets =====

        # -- Trace name section --

        trace_name = QGroupBox()

        trace_name.setFlat(True)
        self.le_trace_name = QLineEdit(self)
        self.le_trace_name.setPlaceholderText("Enter a trace name")
        
        # Generate default trace name based on number of traces in plot
        num_traces = len(parent.trace_list)
        self.le_trace_name.setText(f"Trace {num_traces + 1}")

        form_layout_trace_name = QFormLayout()
        form_layout_trace_name.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout_trace_name.addRow("Trace Name", self.le_trace_name)
        form_layout_trace_name.setContentsMargins(0, 0, 0, 0)

        trace_name.setLayout(form_layout_trace_name)

        # -- Trace Style --

        trace_style = TraceStyleGroupBox()

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

        self.layout_slice = QHBoxLayout()
        group_slice = QGroupBox("Slice Parameters")
        group_slice.setLayout(self.layout_slice)


        # Create a dictionary to hold QListWidgets for slices (updated dynamically)
        self.lwt_slice_dict = dict()


        # -- Ordinate -- 
        ordinate_layout = QHBoxLayout()
        group_ordinate = QGroupBox("Ordinate Parameters")
        group_ordinate.setLayout(ordinate_layout)

        self.lwt_category = ListWidgetTitle("Category")
        self.lwt_value = ListWidgetTitle("Value")
        self.lwt_function = ListWidgetTitle("Function")
        self.lwt_scale = ListWidgetTitle("Scale")

        ordinate_layout.addWidget(self.lwt_category)
        ordinate_layout.addWidget(self.lwt_value)
        ordinate_layout.addWidget(self.lwt_function)
        ordinate_layout.addWidget(self.lwt_scale)
        
        # -- Dialog Butons --

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # === Top-level layout ===
        layout = QVBoxLayout(self)

        layout.addWidget(trace_name)
        layout.addWidget(trace_style)
        layout.addWidget(group_source_field)
        layout.addWidget(group_slice)
        layout.addWidget(group_ordinate)

        layout.addWidget(self.buttons)

        # === Connections ===
        self.lwt_source_field.lw.itemSelectionChanged.connect(self._update_abscissa_options)
        self.lwt_abscissa.lw.itemSelectionChanged.connect(self._update_slice_options)

        # self.buttons.accepted.connect(self._on_accept)
        # self.buttons.rejected.connect(self.reject)

        # self.le_trace_name.returnPressed.connect(self._try_accept)

        # # -- Set current selection row to trigger callbacks --
        self.lwt_source_field.lw.setCurrentRow(0)
        self.lwt_abscissa.lw.setCurrentRow(0)


    # --- Properties ---
    @property
    def selected_field(self):
        # Should only have one selected field
        fields_list = [x.data(Qt.UserRole) for x in self.lwt_source_field.lw.selectedItems()]
        return fields_list[0]
    
    @property
    def selected_abscissa(self):
        # Should only have one selected field
        abscissa_list = [x.data(Qt.UserRole) for x in self.lwt_abscissa.lw.selectedItems()]
        if abscissa_list:
            return abscissa_list[0]
        else:
            return None

    # --- Public Methods ---
    # def get_selections(self) -> dict:
    #     """Return values chosen by the user."""
    #     output_dict = {}
    #     output_dict['report_name'] = self.le_trace_name.text().strip()
    #     if self.show_fields:
    #         output_dict['fields'] = [x.data(Qt.UserRole) for x in self.lw_report_fields.selectedItems()]
    #     return output_dict

    # --- Private Methods ---

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
            (f"{x.title()}", x)
            for x in self.selected_field.data.coords
            if x != 'component'
        ]

        # If plot has an abscissa already selected, only allow that abscissa
        for label, data in abscissa_options:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            if self.parent.abscissa != None and data != self.parent.abscissa:
                item.setEnabled(False)
            self.lwt_abscissa.lw.addItem(item)

        self.lwt_abscissa.lw.setCurrentRow(0)

    def _update_slice_options(self):
        # Need to create N QListWidget boxes to select slice dimenstions in order to reduce ndims to 1
        slice_keys = [
            x
            for x in self.selected_field.data.coords
            if x != 'component' and x != self.selected_abscissa
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

                # Add data to list widget
                data = self.selected_field.data[key]
                units = self.selected_field.data.attrs['coordinate_units'][key]
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


    # def _is_input_valid(self, silent: bool) -> bool:
    #     name = self.le_trace_name.text().strip()

    #     if not name:
    #         if not silent:
    #             QMessageBox.warning(self, "Missing Name", "Please enter a transform node name.")
    #         return False

    #     if not self.lw_report_fields.selectedItems():
    #         if not silent:
    #             QMessageBox.warning(
    #                 self,
    #                 "Missing Field(s)",
    #                 "Please select at least one field for the report.",
    #             )
    #         return False

    #     return True

    # def _try_accept(self) -> None:
    #     if self._is_input_valid(silent=True):
    #         self.accept()

    # def _on_accept(self) -> None:
    #     if self._is_input_valid(silent=False):
    #         self.accept()

class ListWidgetTitle(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label)
        self.lw = QListWidget()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lw)


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

        layout.addLayout(
            self._labeled_control("Color", self.color_btn)
        )

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
            icon = self._make_line_style_icon(style)
            self.cb_line_style.addItem(icon, name)
            self.cb_line_style.setItemData(
                self.cb_line_style.count() - 1,
                style,
                Qt.UserRole
            )

        layout.addLayout(
            self._labeled_control("Line Style", self.cb_line_style)
        )

        # -- Line Width --
        self.sb_line_width = QSpinBox()
        self.sb_line_width.setRange(1, 10)
        self.sb_line_width.setValue(1)
        layout.addLayout(
            self._labeled_control("Width", self.sb_line_width)
        )

        # -- Marker --
        self.cb_marker = QComboBox()
        self.marker_map = {
            "None": None,
            "Circle": "o",
            "Square": "s",
            "Triangle": "t",
            "Diamond": "d",
            "Plus": "+",
            "X": "x",
        }
        self.cb_marker.addItems(self.marker_map.keys())
        self.cb_marker.clear()
        for name, symbol in self.marker_map.items():
            icon = self._make_marker_icon(symbol)
            self.cb_marker.addItem(icon, name)
            self.cb_marker.setItemData(
                self.cb_marker.count() - 1,
                symbol,
                Qt.UserRole
            )
        layout.addLayout(
            self._labeled_control("Marker", self.cb_marker)
        )

        # -- Final Trace Preview --
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(48, 16)
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addLayout(
            self._labeled_control("Preview", self.preview_label)
        )

        self._update_preview()

        self.cb_line_style.currentIndexChanged.connect(self._update_preview)
        self.sb_line_width.valueChanged.connect(self._update_preview)
        self.cb_marker.currentIndexChanged.connect(self._update_preview)

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
        self.color_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #666;
            }}
            """
        )


    def _update_preview(self, width=40, height=20):
        # Get screen dpi to render image properly
        dpr = QGuiApplication.primaryScreen().devicePixelRatio()

        pixmap = QPixmap(int(width * dpr), int(height * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)

        pm = QPixmap(self.preview_label.size())

        pm.fill(Qt.black)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)

        color = self.current_color

        # === Draw line ===
        pen = QPen(
            color,
            self.sb_line_width.value(),
            self.line_styles[self.cb_line_style.currentText()],
        )
        painter.setPen(pen)

        y = pm.height() // 2
        painter.drawLine(2, y, pm.width() - 2, y)

        # === Add marker ===
        symbol = self.marker_map[self.cb_marker.currentText()]
        if symbol:
            painter.setBrush(color)
            cx = pm.width() // 2
            s = 3

            if symbol == "o":            # circle
                painter.drawEllipse(cx - s, y - s, 2*s, 2*s)
            elif symbol == "s":          # square
                painter.drawRect(cx - s, y - s, 2*s, 2*s)
            elif symbol == "t":          # triangle
                painter.drawPolygon([
                    QPoint(cx, y - s),
                    QPoint(cx - s, y + s),
                    QPoint(cx + s, y + s),
                ])
            elif symbol == "d":          # diamond
                painter.drawPolygon([
                    QPoint(cx, y - s),
                    QPoint(cx - s, y),
                    QPoint(cx, y + s),
                    QPoint(cx + s, y),
                ])
            elif symbol in ("+", "x"):
                painter.drawText(pm.rect(), Qt.AlignCenter, symbol)

        painter.end()
        self.preview_label.setPixmap(pm)

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

    @staticmethod
    def _make_marker_icon(symbol, color=QColor("black")):
        """Generate QListWidget line marker preview icon."""
        pm = QPixmap(20, 20)
        pm.fill(Qt.transparent)

        if not symbol:
            return pm

        painter = QPainter(pm)
        painter.setPen(color)
        painter.setBrush(color)

        cx, cy, s = 10, 10, 4

        if symbol == "o":
            painter.drawEllipse(cx - s, cy - s, 2*s, 2*s)
        elif symbol == "s":
            painter.drawRect(cx - s, cy - s, 2*s, 2*s)
        elif symbol == "t":
            painter.drawPolygon([
                QPoint(cx, cy - s),
                QPoint(cx - s, cy + s),
                QPoint(cx + s, cy + s),
            ])
        elif symbol == "d":
            painter.drawPolygon([
                QPoint(cx, cy - s),
                QPoint(cx - s, cy),
                QPoint(cx, cy + s),
                QPoint(cx + s, cy),
            ])
        elif symbol in ("+", "x"):
            painter.drawText(pm.rect(), Qt.AlignCenter, symbol)

        painter.end()
        return pm
