"""
Define new planar near field transform dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from __future__ import annotations

import platform

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from quantiphy import Quantity

from ....common.enums import FieldType, NodeType


class NewPlanarNearFieldTransform(QDialog):
    """
    Input dialog for planar near field transform.

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
        self.setWindowTitle("New Planar Near Field Transform")
        self.setMinimumWidth(480)

        # Load all source field options (near and far) from active project

        fields_node = None
        for tmp_node in target_node.parent.children:
            if tmp_node.node_type == NodeType.FIELDS:
                fields_node = tmp_node
                break
        assert fields_node is not None

        source_field_options = [(f"{x.name}", x) for x in fields_node.children]

        # Populate Combo Boxes
        self.cb_source_field = QComboBox()
        for label, item in source_field_options:
            if item.node_type == NodeType.FIELDS and item.field_type == FieldType.NEAR:
                self.cb_source_field.addItem(label, item)
            # if item.node_type == NodeType.FIELDS and item.field_type == FieldType.FAR:
            #     # A probe correction can be any far field measurement
            #     self.cb_probe_corrections.addItem(label, item)

        # -- Populate probe options --

        probes_node = None
        for tmp_node in target_node.parent.children:
            if tmp_node.node_type == NodeType.PROBES:
                probes_node = tmp_node
                break
        assert probes_node is not None
        probe_options = [
            (f"{x.name} ({x.correction_type})", x) for x in probes_node.children
        ]

        # self.cb_far_field = QComboBox()
        self.cb_probe_corrections = QComboBox()

        for label, item in probe_options:
            self.cb_probe_corrections.addItem(label, item)

        # The user may elect to use no probe corrections
        self.cb_probe_corrections.addItem("None", None)

        # -- Populate gain calibration options --

        self.cb_gain_cal = QComboBox()

        cals_node = None
        for tmp_node in target_node.parent.children:
            if tmp_node.node_type == NodeType.CALS:
                cals_node = tmp_node
                break
        assert cals_node is not None

        cals_options = [(f"{x.name}", x) for x in cals_node.children]

        for label, item in cals_options:
            if item.node_type == NodeType.CALS:
                self.cb_gain_cal.addItem(label, item)

        # The user may elect to use no probe corrections
        self.cb_gain_cal.addItem("None", None)

        # -- Create remaining widgets --

        self.lw_frequencies = QListWidget(self)
        self.lw_frequencies.setFocusPolicy(Qt.StrongFocus)
        self.lw_frequencies.setSelectionMode(QListWidget.ExtendedSelection)
        self._update_frequencies()

        # Generate help label based on platform type
        mod_key = "⌘" if platform.system() == "Darwin" else "Ctrl"
        label_freq_help = QLabel(
            f"To select multiple frequencies hold {mod_key} or Shift, or {mod_key}-A to select all."
        )
        label_freq_help.setStyleSheet("color: #777")

        self.le_transform_name = QLineEdit(self)
        self.le_transform_name.setText("Planar Near Field Transform")
        self.le_transform_name.setPlaceholderText("Enter the name for the transform")

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Populate Layout ---
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        form_layout.addRow("Transform Name:", self.le_transform_name)

        form_layout.addRow("Source Field:", self.cb_source_field)
        # form_layout.addRow(
        #     "Far Field (Reference):",
        #     self.cb_far_field,
        # )
        form_layout.addRow("Frequencies:", self.lw_frequencies)
        form_layout.addRow(label_freq_help)
        form_layout.addRow("Probe Corrections:", self.cb_probe_corrections)
        form_layout.addRow("Gain Calibration:", self.cb_gain_cal)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)

        layout.addWidget(self.buttons)

        # --- Add Connections ---
        self.cb_source_field.currentTextChanged.connect(self._update_frequencies)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)
        self.le_transform_name.returnPressed.connect(self._try_accept)

    def get_selections(self) -> dict:
        """Return values chosen by the user."""
        return {
            "transform_name": self.le_transform_name.text().strip(),
            "source_field": self.cb_source_field.currentData(),
            "probe_correction": (
                self.cb_probe_corrections.currentData().probe
                if self.cb_probe_corrections.currentData()
                else None
            ),
            "gain_calibration": (
                self.cb_gain_cal.currentData()
                if self.cb_gain_cal.currentData()
                else None
            ),
            "frequencies": [
                x.data(Qt.UserRole) for x in self.lw_frequencies.selectedItems()
            ],
        }

    def _update_frequencies(self) -> None:
        """Update frequencies in `lw_frequencies`."""
        # Remove all items before updating items
        self.lw_frequencies.clear()

        if self.cb_source_field.currentData():
            frequencies = (
                self.cb_source_field.currentData()
                .data.coords["frequency"]
                .values.tolist()
            )
            frequencies_items = [(str(Quantity(x, units="Hz")), x) for x in frequencies]
            for label, data in frequencies_items:
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, data)
                self.lw_frequencies.addItem(item)

    def _is_input_valid(self, silent=True) -> bool:
        """Check if inputs are valid.

        Parameters
        ----------
        silent : bool, optional
            Whether to generate message boxes, by default True

        Returns
        -------
        bool
            If input is valid.
        """
        name = self.le_transform_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a transform node name."
                )
            return False

        if not self.cb_source_field.currentData():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Source Field",
                    "Please select a source field to transform.",
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

        # Check if gain calibration overlaps _any_ of transform frequency range
        if self.cb_gain_cal.currentData():
            selected_freq_list = [
                x.data(Qt.UserRole) for x in self.lw_frequencies.selectedItems()
            ]
            gain_cal_freqs = self.cb_gain_cal.currentData().gain_cal_ref.data.frequency

            freq_overlap = max(
                np.nanmin(gain_cal_freqs), np.nanmin(selected_freq_list)
            ) <= min(np.nanmax(gain_cal_freqs), np.nanmax(selected_freq_list))

            if not freq_overlap:
                msgBox = QMessageBox(self)
                msgBox.setText("Invalid gain calibration frequencies.")
                msgBox.setInformativeText(
                    "Gain calibration does not overlap with selected frequencies.  Continue anyway?"
                )
                msgBox.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.StandardButton.Cancel
                )
                msgBox.setDefaultButton(QMessageBox.Save)
                ret = msgBox.exec()

                return ret == QMessageBox.Yes

        return True

    def _try_accept(self) -> None:
        """
        Wrapper for QDialog `accept` function.

        Silently check if inputs are valid before accepting.
        """
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        """
        Wrapper for QDialog `accept` function.

        Check if inputs are valid before accepting with message box on failure.
        """
        if self._is_input_valid(silent=False):
            self.accept()
