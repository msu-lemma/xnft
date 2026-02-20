"""
Define new field report dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple
from pathlib import Path

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
    QLabel,
    QMessageBox,
    QSpinBox,
    QListWidget,
    QListWidgetItem,
)


from ....core.types import ReportType, FieldType, NodeType


class NewFieldReport(QDialog):
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

        # --- Widgets ---

        self.le_report_name = QLineEdit(self)
        self.le_report_name.setText("Field Report")
        self.le_report_name.setPlaceholderText("Enter the name for the report")

        self.cb_report_type = QComboBox()
        self.cb_field_type = QComboBox()

        # Populate Combo Boxes
        for _, item in ReportType._member_map_.items():
            if item != ReportType.UNKNOWN:
                pretty_label = item.value
                self.cb_report_type.addItem(pretty_label, item)

        for _, item in FieldType._member_map_.items():
            if item != FieldType.UNKNOWN:
                pretty_label = item.value
                self.cb_field_type.addItem(pretty_label, item)

        self.lw_report_fields = QListWidget(self)
        self.lw_report_fields.setSelectionMode(QListWidget.ExtendedSelection)
        self._update_field_options()

        self.lw_report_frequencies = QListWidget(self)
        self.lw_report_frequencies.setSelectionMode(
            QListWidget.ExtendedSelection
        )
        self._update_frequency_options()

        # self.help_label = QLabel(
        #     "FFT sizes will be truncated down from the next largest "
        #     "power of 2."
        # )
        # self.help_label.setStyleSheet("color: #777")

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # # --- Layout ---
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        form_layout.addRow("Report Name:", self.le_report_name)

        form_layout.addRow(
            "Report Type:",
            self.cb_report_type,
        )
        form_layout.addRow(
            "Field Type:",
            self.cb_field_type,
        )
        form_layout.addRow(
            "Fields:",
            self.lw_report_fields,
        )
        form_layout.addRow(
            "Frequencies:",
            self.lw_report_frequencies,
        )

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        # form_layout.addRow(self.help_label)

        layout.addWidget(self.buttons)

        # # --- Connections ---
        self.cb_field_type.currentTextChanged.connect(
            self._update_field_options
        )

        self.lw_report_fields.itemSelectionChanged.connect(
            self._update_frequency_options
        )

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # # Enter key creates if valid
        self.le_report_name.returnPressed.connect(self._try_accept)

    # --- Public Methods ---
    def get_selections(self) -> dict:
        """Return values chosen by the user."""
        return {
            "report_name": self.le_report_name.text().strip(),
            "report_type": self.cb_report_type.currentData(),
            "field_type": self.cb_field_type.currentData(),
            "fields": [
                x.data(Qt.UserRole)
                for x in self.lw_report_fields.selectedItems()
            ],
            "frequencies": [
                x.data(Qt.UserRole)
                for x in self.lw_report_frequencies.selectedItems()
            ],
        }

    # --- Private Methods ---

    def _update_field_options(self):
        self.lw_report_fields.clear()

        self.fields_node = None
        for tmp_node in self.target_node.parent.children:
            if tmp_node.type == NodeType.FIELDS:
                self.fields_node = tmp_node
                break
        assert self.fields_node is not None

        field_options = [
            (f"{x.name}", x)
            for x in self.fields_node.children
            if x.type == self.cb_field_type.currentData()
        ]

        for label, data in field_options:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_report_fields.addItem(item)

    def _update_frequency_options(self):
        # Remove all items before updating items
        self.lw_report_frequencies.clear()

        frequencies = []

        for item in self.lw_report_fields.selectedItems():
            frequencies += (
                item.data(Qt.UserRole).data.coords["frequency"].values.tolist()
            )

        # Get only unique items
        frequencies = list(set(frequencies))

        frequencies_items = [
            (str(Quantity(x, units="Hz")), x) for x in frequencies
        ]
        for label, data in frequencies_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_report_frequencies.addItem(item)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_report_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a transform node name."
                )
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
