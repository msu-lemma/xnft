"""
Define new measurement probe dialog window.

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
from ....core.enums import ProbeType
from ....core.antennas.probes.standard_probes import StandardRectWaveguide
from ....core.types import FileInfo
from ....core.antennas.probes.probes import RectWaveguide, MeasurementProbe

from quantiphy import Quantity


class NewProbeDialog(QDialog):
    """
    Input dialog for measurement probe creation.

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
        self.setWindowTitle("New Measurement Probe")
        self.setMinimumWidth(540)

        # --- Create Widgets ---
        self.cb_probe_type = QComboBox()

        for probe_type in ProbeType:
            if probe_type != ProbeType.UNKNOWN:
                self.cb_probe_type.addItem(probe_type.value, (probe_type,))

        self.le_probe_name = QLineEdit(self)
        self.le_probe_name.setText("Measurement Probe")
        self.le_probe_name.setPlaceholderText("Enter a name for the measurement probe")

        # -- Ideal probe --

        self.group_ap_dim = QGroupBox("Aperture Dimensions")

        layout_dim = QVBoxLayout()

        self.cb_standard_waveguide_type = QComboBox()
        self.cb_standard_waveguide_type.addItem("Custom Rectangular Waveguide", None)

        # Add standard waveguide sizes
        for field_type in StandardRectWaveguide:
            label = (
                f"{field_type.name} "
                f"({Quantity(field_type.value.band[0], units='Hz')}"
                f"–{Quantity(field_type.value.band[1], units='Hz')})"
            )
            self.cb_standard_waveguide_type.addItem(label, field_type)

        layout_dim.addWidget(LabeledWidget("Probe Type", self.cb_standard_waveguide_type))

        self.units_label = QLabel("Units: mm")
        self.units_label.setStyleSheet("color: #777")
        layout_dim.addWidget(self.units_label)

        self.le_ap_x = QLineEdit(self)
        self.le_ap_x.setPlaceholderText("Enter x dimension of the aperture (cross-pol)")
        layout_dim.addWidget(LabeledWidget("X", self.le_ap_x))

        self.le_ap_y = QLineEdit(self)
        self.le_ap_y.setPlaceholderText("Enter y dimension of the aperture (co-pol)")
        layout_dim.addWidget(LabeledWidget("Y", self.le_ap_y))

        self.group_ap_dim.setLayout(layout_dim)

        self._update_waveguide_selection()

        # -- Meausred Probe --

        self.group_meas = QGroupBox("Measured Probe")

        layout_meas = QVBoxLayout()

        # TODO: load supported probe file types dynamically
        self.fe_measured_probe = FileEntryRow(
            "Choose or enter the path to the measured probe file",
            get_available_extensions="*.nist",
        )

        layout_meas.addWidget(LabeledWidget("Probe Measurement file:", self.fe_measured_probe))

        self.units_label = QLabel("File types: *.nist")
        self.units_label.setStyleSheet("color: #777")
        layout_meas.addWidget(self.units_label)

        self.group_meas.setLayout(layout_meas)

        # -- Buttons --
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Create Layout ---

        layout = QVBoxLayout(self)

        layout.addWidget(LabeledWidget("Probe Name:", self.le_probe_name))
        layout.addWidget(LabeledWidget("Probe Type:", self.cb_probe_type, compact=True))

        layout.addWidget(self.group_ap_dim)
        layout.addWidget(self.group_meas)

        layout.addStretch(1)

        layout.addWidget(self.buttons)

        # --- Add Connections ---

        self.cb_probe_type.currentTextChanged.connect(self._update_fields_shown)
        self.cb_standard_waveguide_type.currentTextChanged.connect(
            self._update_waveguide_selection
        )
        self._update_fields_shown()

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        # self.path_field.returnPressed.connect(self._try_accept)

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

    @property
    def selected_probe_type(self) -> ProbeType:
        return self.cb_probe_type.currentData()[0]

    def _update_fields_shown(self):
        # Enable/disable data polarization specific data selection boxes
        if self.selected_probe_type == ProbeType.MEASURED:
            self.group_meas.show()
            self.group_ap_dim.hide()
        else:
            self.group_ap_dim.show()
            self.group_meas.hide()
        self.adjustSize()

    def _update_waveguide_selection(self) -> None:
        """Update waveguide dimensions based on selected waveguide."""
        wg = self.cb_standard_waveguide_type.currentData()

        if wg is not None:
            self.le_ap_x.setEnabled(False)
            self.le_ap_y.setEnabled(False)
            self.le_ap_x.setText(str(round(wg.value.x * 1e3, 4)))
            self.le_ap_y.setText(str(round(wg.value.y * 1e3, 4)))
            self.le_probe_name.setText(wg.name)
        else:
            self.le_ap_x.setEnabled(True)
            self.le_ap_y.setEnabled(True)
            self.le_ap_x.setText("")
            self.le_ap_y.setText("")
            self.le_probe_name.setText("Measurement Probe")

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


class FileEntryRow(QWidget):
    def __init__(
        self,
        placeholder="Choose or enter the path to the file",
        get_available_extensions=None,
        parent=None,
    ):
        """Create field entry row with path item and browse button.

        Parameters
        ----------
        placeholder : str, optional
            Placeholder test to show in file box, by default "Choose or enter the path to the file"
        get_available_extensions : Callable, optional
            Function which returns valid extensions, by default None
        has_sp : bool, optional
            Whether file has S-Parameters, by default False
        """
        super().__init__(parent)
        self.parent = parent

        self._show_sp = False

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.get_available_extensions = get_available_extensions

        self.le_path = QLineEdit(self)
        self.le_path.setPlaceholderText(placeholder)

        self.cb_sp = QComboBox(self)
        self.cb_sp.setHidden(not self._show_sp)

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(QIcon.fromTheme("folder-open"))

        self._layout.addWidget(self.le_path, 1)
        self._layout.addWidget(self.cb_sp, 0)
        self._layout.addWidget(self.btn_browse, 0)

        self.btn_browse.clicked.connect(self._on_browse_clicked)
        # self.le_path.textChanged.connect(self._on_le_path_update)

    def _on_browse_clicked(self) -> None:
        """Create folder selection dialog."""
        start_dir = self.le_path.text().strip() or str(Path.home())
        chosen = QFileDialog.getOpenFileName(
            self,
            "Select Fields File",
            start_dir,
            filter=" ".join(self.get_available_extensions()),
        )
        if chosen[0]:
            self.le_path.setText(chosen[0])
