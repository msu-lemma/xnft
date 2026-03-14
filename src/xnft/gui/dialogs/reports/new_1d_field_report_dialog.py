"""
Define new 2D field report dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

from quantiphy import Quantity

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QWidget,
    QComboBox,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QLabel,
)

import platform

from ....core.enums import ReportType, FieldType, NodeType
from ....core.plots.plot_2d import Plot2D
from ....core.plots.functions import PlotFunctions


class New2DFieldReport(QDialog):
    """
    Input dialog for field report.

    Parameters
    ----------
    parent : QWidget | None, optional
        Parent widget for dialog, by default None
    target_node : Node | None, optional
        Target node invoking this dialog, by default None
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        target_node=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("New Field Report")
        self.setMinimumWidth(480)

        self.target_node = target_node

        # ===== Widgets =====

        # -- Report Name Section --

        group_report_name = QGroupBox()

        group_report_name.setFlat(True)
        self.le_report_name = QLineEdit(self)
        self.le_report_name.setText("Field Report")
        self.le_report_name.setPlaceholderText("Enter the name for the report")

        form_layout_report_name = QFormLayout()
        form_layout_report_name.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout_report_name.addRow("Report Name", self.le_report_name)
        form_layout_report_name.setContentsMargins(0, 0, 0, 0)

        group_report_name.setLayout(form_layout_report_name)

        # -- Data Selection Section --

        self.lw_report_fields = QListWidget(self)
        self._update_field_options()

        self.lw_report_frequencies = QListWidget(self)
        self.lw_report_frequencies.setSelectionMode(QListWidget.ExtendedSelection)
        self._update_frequency_options()

        self.cb_report_field_components = QComboBox()

        # Generate help label based on platform type
        mod_key = "⌘" if platform.system() == "Darwin" else "ctrl"
        label_freq_help = QLabel(
            f"To select multiple frequencies hold {mod_key} or shift, or {mod_key}-A to select all."
        )
        label_freq_help.setStyleSheet("color: #777")

        form_layout_data = QFormLayout()
        form_layout_data.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        form_layout_data.addRow("Report Field:", self.lw_report_fields)
        form_layout_data.addRow("Report Frequencies:", self.lw_report_frequencies)
        form_layout_data.addRow(label_freq_help)
        form_layout_data.addRow("Report Field Components:", self.cb_report_field_components)

        group_data_selection = QGroupBox("Data Source")
        group_data_selection.setLayout(form_layout_data)

        # --- Plotting Parameters Layout ---

        self.cb_plot_coordinates_type = QComboBox()
        self.cb_plot_function = QComboBox()
        self.cb_plot_scale = QComboBox()

        self._update_plotting_function_options()
        self._update_plotting_scale_options()

        form_layout_plot = QFormLayout()
        form_layout_plot.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        form_layout_plot.addRow("Coordinates:", self.cb_plot_coordinates_type)
        form_layout_plot.addRow("Function:", self.cb_plot_function)
        form_layout_plot.addRow("Scale:", self.cb_plot_scale)

        group_plot_parameters = QGroupBox("Report Parameters")
        group_plot_parameters.setLayout(form_layout_plot)

        # -- Dialog Butons --

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # === Top-level layout ===
        layout = QVBoxLayout(self)

        layout.addWidget(group_report_name)
        layout.addWidget(group_data_selection)
        layout.addWidget(group_plot_parameters)

        layout.addWidget(self.buttons)

        # === Connections ===

        self.lw_report_fields.itemSelectionChanged.connect(self._update_frequency_options)
        self.lw_report_fields.itemSelectionChanged.connect(
            self._update_plotting_coordainte_options
        )
        self.lw_report_fields.itemSelectionChanged.connect(self._update_report_field_components)
        self.cb_plot_function.currentTextChanged.connect(self._update_plotting_scale_options)

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        self.le_report_name.returnPressed.connect(self._try_accept)

        # -- Set current selection row to trigger callbacks --
        self.lw_report_fields.setCurrentRow(0)

    # --- Public Methods ---
    def get_selections(self) -> dict:
        """Return values chosen by the user."""
        return {
            "report_name": self.le_report_name.text().strip(),
            "coordinates_type": self.cb_plot_coordinates_type.currentData()[0],
            "fields": [x.data(Qt.UserRole) for x in self.lw_report_fields.selectedItems()],
            "frequencies": [
                x.data(Qt.UserRole) for x in self.lw_report_frequencies.selectedItems()
            ],
            "field_components": self.cb_report_field_components.currentData(),
            "function": self.cb_plot_function.currentData()[0],
            "scale": self.cb_plot_scale.currentData(),
            "norm": None,  # TODO: Add normalization options
        }

    # --- Private Methods ---

    # def _update_plotting_function_options(self):
    #     # Remove all items before updating items
    #     for _ in range(self.cb_plot_function.count()):
    #         self.cb_plot_function.removeItem(0)

    #     for plot_function in PlotFunctions:
    #         self.cb_plot_function.addItem(plot_function.value.name, (plot_function,))

    # def _update_report_field_components(self):
    #     # Remove all items before updating items
    #     for _ in range(self.cb_report_field_components.count()):
    #         self.cb_report_field_components.removeItem(0)

    #     field_components = ["All"]
    #     field_components += (
    #         self.lw_report_fields.selectedItems()[0]
    #         .data(Qt.UserRole)
    #         .data.coords["component"]
    #         .data.tolist()
    #     )

    #     self.cb_report_field_components.addItems(field_components)

    # def _update_plotting_scale_options(self):
    #     # Remove all items before updating items
    #     for _ in range(self.cb_plot_scale.count()):
    #         self.cb_plot_scale.removeItem(0)

    #     plot_function = self.cb_plot_function.currentData()[0]

    #     for scale in plot_function.value.scales:
    #         self.cb_plot_scale.addItem(scale.value.name, scale)

    # def _update_plotting_coordainte_options(self):
    #     # Remove all items before updating items
    #     for _ in range(self.cb_plot_coordinates_type.count()):
    #         self.cb_plot_coordinates_type.removeItem(0)

    #     # Get selected field source coordinates
    #     source_coordiante_system = (
    #         self.lw_report_fields.selectedItems()[0].data(Qt.UserRole).coordinates.node_type
    #     )

    #     valid_plot_coordinates = Plot2D.__coordinates__[source_coordiante_system]

    #     for coordinates_type in valid_plot_coordinates:
    #         self.cb_plot_coordinates_type.addItem(coordinates_type.value, (coordinates_type,))

    def _update_field_options(self):
        self.lw_report_fields.clear()

        self.fields_node = None
        for tmp_node in self.target_node.parent.children:
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
            self.lw_report_fields.addItem(item)

    # def _update_frequency_options(self):
    #     # Remove all items before updating items
    #     self.lw_report_frequencies.clear()

    #     frequencies = []

    #     for item in self.lw_report_fields.selectedItems():
    #         frequencies += item.data(Qt.UserRole).data.coords["frequency"].values.tolist()

    #     # Get only unique items
    #     frequencies = list(set(frequencies))

    #     frequencies_items = [(str(Quantity(x, units="Hz")), x) for x in frequencies]
    #     for label, data in frequencies_items:
    #         item = QListWidgetItem(label)
    #         item.setData(Qt.UserRole, data)
    #         self.lw_report_frequencies.addItem(item)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_report_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(self, "Missing Name", "Please enter a transform node name.")
            return False

        if not self.lw_report_fields.selectedItems():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Field(s)",
                    "Please select at least one field for the report.",
                )
            return False

        if not self.lw_report_frequencies.selectedItems():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Frequencies",
                    "Please select at least one frequency for the report.",
                )
            return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()
