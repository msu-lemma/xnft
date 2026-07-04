"""
Define new power calibration dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from pathlib import Path
from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QComboBox,
    QLabel,
    QGroupBox,
)

from ..common import LabeledWidget
from ....loaders.fields.field_loader_registry import field_loader_registry
from ....project.nodes.node import Node
from ....core.enums import ProbeType, FieldType, NodeType
from ....core.apertures.probes import RectWaveguide, MeasurementProbe

from quantiphy import Quantity

class NewPowerCalibrationDialog(QDialog):
    """
    Input dialog for power calibration creation.

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
        self.setWindowTitle("New Power Calibration")
        self.setMinimumWidth(540)

        # --- Create Widgets ---

        self.le_calibration_name = QLineEdit(self)
        self.le_calibration_name.setText("Power Calibration")
        self.le_calibration_name.setPlaceholderText("Enter the name for the power calibration")

        # Load all source field options (near and far) from active project

        fields_node = None

        for tmp_node in target_node.parent.children:
            if tmp_node.node_type == NodeType.FIELDS:
                fields_node = tmp_node
                break
        assert fields_node is not None

        source_field_options = [(f"{x.name}", x) for x in fields_node.children]

        # -- Populate power calibration options --

        self.cb_power_cal_field = QComboBox()
        self.cb_power_cal_standard = QComboBox()

        # Add normal items
        # self.cb_power_cal_standard.addItems(["Option A", "Option B", "Option C"])

        self._update_cal_standard()

        # Store last valid selection for combobox after import is pressed
        self.cb_power_cal_standard_last_index = 0
        self.cb_power_cal_standard.setCurrentIndex(self.cb_power_cal_standard_last_index)

        for label, item in source_field_options:
            if item.node_type == NodeType.FIELDS and item.field_type == FieldType.FAR:
                self.cb_power_cal_field.addItem(label, item)

        power_cal_options: list[tuple] = list()
        for label, item in power_cal_options:
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

        self.form_layout = QFormLayout(self)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        group = QGroupBox("Power Calibration Measurements")
        group.setLayout(self.form_layout)

        self.form_layout.addRow("Measured Field:", self.cb_power_cal_field)
        self.form_layout.addRow("Reference File:", self.cb_power_cal_standard)

        layout.addWidget(group)

        layout.addWidget(self.buttons)

        # --- Add Connections ---
        self.cb_power_cal_standard.currentIndexChanged.connect(self._on_cal_standard_changed)

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

    def get_selections(self) -> dict:
        """Return values chosen by user."""
        probe_type = self.selected_probe_type

        if probe_type == ProbeType.IDEAL_RECT:

            if self.cb_standard_waveguide_type.currentData() is None:
                source = RectWaveguide(
                    x=float(self.le_ap_x.text().strip()) * 1e-3,
                    y=float(self.le_ap_y.text().strip()) * 1e-3,
                    band=(float("nan"), float("nan")),
                )
            else:
                source = self.cb_standard_waveguide_type.currentData().value

            probe = MeasurementProbe(name=self.le_probe_name.text().strip(), source=source)

        elif probe_type == ProbeType.MEASURED:
            probe = None
            raise NotImplementedError("Measured probe type not yet implemented.")
        else:
            raise TypeError(
                f"probe_type must be ProbeType.MEASURED or ProbeType.IDEAL_RECT, got {type(probe_type)}"
            )

        return {"probe": probe}

    def _update_cal_standard(self):
        # TODO: Add loaded cal standards here

        # Add import button at bottom of list
        self.cb_power_cal_standard.insertSeparator(self.cb_power_cal_standard.count())
        self.import_index = self.cb_power_cal_standard.count()
        self.cb_power_cal_standard.addItem("Import reference file...")

    def _on_cal_standard_changed(self, index):
        if index == self.import_index:
            # Open file dialog
            start_dir = str(Path.home())
            file_type_str = "*.cal"
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Calibration File",
                start_dir,
                filter=file_type_str,
            )

            if file_path:
                print(f"User selected: {file_path}")
                # TODO

            # Restore previous selection (avoid leaving it on "Import...")
            self.cb_power_cal_standard.blockSignals(True)
            self.cb_power_cal_standard.setCurrentIndex(self.cb_power_cal_standard_last_index)
            self.cb_power_cal_standard.blockSignals(False)
        else:
            # Update last valid selection
            self.cb_power_cal_standard_last_index = index

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_probe_name.text().strip()
        if not name:
            if not silent:
                QMessageBox.warning(self, "Missing Name", "Please enter a field node name.")
            return False

        if self.selected_probe_type == ProbeType.IDEAL_RECT:
            if not silent:
                try:
                    float(self.le_ap_x.text().strip())
                    float(self.le_ap_y.text().strip())
                except ValueError as e:
                    QMessageBox.warning(
                        self,
                        "Value Error",
                        f"{str(e).capitalize()}. X and Y values must be numerical.",
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
