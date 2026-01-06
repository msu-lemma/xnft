"""Define new planar near field transform dialog window."""

from __future__ import annotations
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

# from ...core.project import Node


class NewPlanarNearFieldTransform(QDialog):
    """
    Input dialog for planar near field transform.

    Includes basic data validation.

    Copyright 2025-2026 The LEmmA Group, Michigan State University.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        target_node=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("New Planar Near Field Transform")
        self.setMinimumWidth(480)

        # Load all options from active project

        fields_node = None
        for tmp_node in target_node.parent.children:
            if tmp_node.name == "Fields":
                fields_node = tmp_node
                break
        assert fields_node is not None

        source_field_options: list[Tuple[str, object]] = [
            (f"{x.name} ({x.display_type})", x) for x in fields_node.children
        ]

        # --- Widgets ---
        self.cb_source_field = QComboBox()
        self.cb_far_field = QComboBox()
        self.cb_probe_corrections = QComboBox()

        # The user may elect to use no probe corrections
        self.cb_probe_corrections.addItem("None", None)

        # Populate Combo Boxes
        for label, item in source_field_options:
            if item.type == "Near Field":
                self.cb_source_field.addItem(label, item)
                # A probe correction can be any near field measurement
                self.cb_probe_corrections.addItem(label, item)

        for label, item in source_field_options:
            if item.type == "Far Field":
                self.cb_far_field.addItem(label, item)

        self.lw_frequencies = QListWidget(self)
        self.lw_frequencies.setSelectionMode(QListWidget.ExtendedSelection)
        self._update_frequencies()

        self.le_transform_name = QLineEdit(self)
        self.le_transform_name.setText("Planar Near Field Transform")
        self.le_transform_name.setPlaceholderText(
            "Enter the name for the transform"
        )

        self.sb_fft_x_size = QSpinBox(self)
        self.sb_fft_x_size.setMinimum(2)
        self.sb_fft_x_size.setMaximum(16384)
        self.sb_fft_x_size.setValue(4096)

        self.sb_fft_y_size = QSpinBox(self)
        self.sb_fft_y_size.setMinimum(2)
        self.sb_fft_y_size.setMaximum(16384)
        self.sb_fft_y_size.setValue(4096)

        self.help_label = QLabel(
            "FFT sizes will be truncated down from the next largest "
            "power of 2."
        )
        self.help_label.setStyleSheet("color: #777")

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        form_layout.addRow("Transform Name:", self.le_transform_name)

        form_layout.addRow(
            "Source Field:",
            self.cb_source_field,
        )
        form_layout.addRow(
            "Far Field (Reference):",
            self.cb_far_field,
        )
        form_layout.addRow(
            "Frequencies:",
            self.lw_frequencies,
        )
        form_layout.addRow(
            "Probe Corrections:",
            self.cb_probe_corrections,
        )
        form_layout.addRow(
            "FFT X Size:",
            self.sb_fft_x_size,
        )
        form_layout.addRow(
            "FFT Y Size:",
            self.sb_fft_y_size,
        )

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        form_layout.addRow(self.help_label)

        layout.addWidget(self.buttons)

        # --- Connections ---
        self.cb_source_field.currentTextChanged.connect(
            self._update_frequencies
        )

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        self.sb_fft_x_size.returnPressed.connect(self._try_accept)
        self.sb_fft_y_size.returnPressed.connect(self._try_accept)
        self.le_transform_name.returnPressed.connect(self._try_accept)

    # --- Public Methods ---
    def get_selections(self) -> dict:
        """Return values chosen by the user."""
        return {
            "transform_name": self.le_transform_name.text().strip(),
            "source_field": self.cb_source_field.currentData(),
            "far_field": self.cb_far_field.currentData(),
            "probe_correction": self.cb_probe_corrections.currentData(),
            "fft_x_size": self.sb_fft_x_size.value(),
            "fft_y_size": self.sb_fft_y_size.value(),
            "frequencies": [
                x.data(Qt.UserRole)
                for x in self.lw_frequencies.selectedItems()
            ],
        }

    # --- Private Methods ---

    def _update_frequencies(self):
        # Remove all items before updating items
        self.lw_frequencies.clear()

        frequencies = (
            self.cb_source_field.currentData()
            .data.coords["frequency"]
            .values.tolist()
        )
        frequencies_items = [
            (str(Quantity(x, units="Hz")), x) for x in frequencies
        ]
        for label, data in frequencies_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_frequencies.addItem(item)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_transform_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a transform node name."
                )
            return False

        if not self.lw_frequencies.selectedItems():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Frequencies",
                    "Please select at least one frequency.",
                )
            return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()
