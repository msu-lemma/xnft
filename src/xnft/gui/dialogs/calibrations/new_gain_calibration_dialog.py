"""
Define new gain calibration dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ....calibration.gain import (
    copy_gain_cal_file,
    gain_cal_dir,
    get_gain_cal_files,
    load_gain_cal,
)
from ....common.enums import FieldType, NodeType
from ....project.nodes.node import Node
from ..common import LabeledWidget

logger = logging.getLogger(__name__)


class NewGainCalibrationDialog(QDialog):
    """
    Input dialog for gain calibration creation.

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
        target_node: Node | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("New Gain Calibration")
        self.setMinimumWidth(540)

        # --- Create Widgets ---

        self.le_calibration_name = QLineEdit(self)
        self.le_calibration_name.setText("Gain Calibration")
        self.le_calibration_name.setPlaceholderText(
            "Enter the name for the gain calibration"
        )

        # Load all source field options (near and far) from active project

        fields_node = None

        for tmp_node in target_node.parent.children:
            if tmp_node.node_type == NodeType.FIELDS:
                fields_node = tmp_node
                break
        assert fields_node is not None

        source_field_options = [(f"{x.name}", x) for x in fields_node.children]

        # -- Populate gain calibration options --

        self.cb_gain_cal_field = QComboBox()
        self.cb_gain_cal_reference = QComboBox()

        self._update_gain_cals()

        # Store last valid selection for combobox after import is pressed
        self.cb_gain_cal_standard_last_index = 0
        self.cb_gain_cal_reference.setCurrentIndex(self.cb_gain_cal_standard_last_index)

        for label, item in source_field_options:
            if item.node_type == NodeType.FIELDS and item.field_type == FieldType.FAR:
                self.cb_gain_cal_field.addItem(label, item)

        gain_cal_options: list[tuple] = []
        for label, item in gain_cal_options:
            pass

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Create Layout ---

        layout = QVBoxLayout(self)

        layout.addWidget(LabeledWidget("Calibration Name:", self.le_calibration_name))

        self.form_layout = QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        group = QGroupBox("Gain Calibration Measurements")
        group.setLayout(self.form_layout)

        self.form_layout.addRow("Measured Field:", self.cb_gain_cal_field)
        self.form_layout.addRow("Reference File:", self.cb_gain_cal_reference)

        layout.addWidget(group)

        layout.addWidget(self.buttons)

        # --- Add Connections ---
        self.cb_gain_cal_reference.currentIndexChanged.connect(
            self._on_cal_standard_changed
        )

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

    def get_selections(self) -> dict:
        """Return values chosen by user."""
        gain_cal_field = self.cb_gain_cal_field.currentData()
        gain_cal_ref_path = self.cb_gain_cal_reference.currentData()
        gain_cal_ref = load_gain_cal(gain_cal_ref_path)

        return {
            "gain_cal_name": self.le_calibration_name.text().strip(),
            "gain_cal_ref": gain_cal_ref,
            "gain_cal_field": gain_cal_field,
        }

    def _update_gain_cals(self):
        # Remove all items before updating items
        for _ in range(self.cb_gain_cal_reference.count()):
            self.cb_gain_cal_reference.removeItem(0)

        # Add loaded cal standards: (file_path, name)
        cal_file_list = get_gain_cal_files(name_only=True)

        for path, name in cal_file_list:
            self.cb_gain_cal_reference.addItem(name, path)

        # Add import button at bottom of list
        self.cb_gain_cal_reference.insertSeparator(self.cb_gain_cal_reference.count())

        self.import_index = self.cb_gain_cal_reference.count()
        self.cb_gain_cal_reference.addItem("Import reference file...")

        self.manage_index = self.cb_gain_cal_reference.count()
        self.cb_gain_cal_reference.addItem("Manage reference files...")

    def _on_cal_standard_changed(self, index):
        if index == self.import_index:
            # Open file dialog
            start_dir = str(Path.home())
            file_type_str = "*.cal;*.ngt"
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Calibration File",
                start_dir,
                filter=file_type_str,
            )

            if file_path:
                logger.debug(f"Calibration file selected: {file_path}")

                copy_gain_cal_file(file_path)
                self._update_gain_cals()

            # Restore previous selection (avoid leaving it on "Import...")
            self.cb_gain_cal_reference.blockSignals(True)
            self.cb_gain_cal_reference.setCurrentIndex(
                self.cb_gain_cal_standard_last_index
            )
            self.cb_gain_cal_reference.blockSignals(False)
        elif index == self.manage_index:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(gain_cal_dir)))

            # Restore previous selection (avoid leaving it on "Import...")
            self.cb_gain_cal_reference.blockSignals(True)
            self.cb_gain_cal_reference.setCurrentIndex(
                self.cb_gain_cal_standard_last_index
            )
            self.cb_gain_cal_reference.blockSignals(False)
        else:
            # Update last valid selection
            self.cb_gain_cal_standard_last_index = index

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_calibration_name.text().strip()
        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a field node name."
                )
            return False

        if self.cb_gain_cal_field.currentData() is None and not silent:
            QMessageBox.warning(
                self,
                "Value Error",
                "Measured Field cannot be empty.",
            )
            return False

        if self.cb_gain_cal_reference.currentData() is None and not silent:
            QMessageBox.warning(
                self,
                "Value Error",
                "Reference File cannot be empty.",
            )
            return False

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
