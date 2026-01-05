"""Define new field measurement dialog window."""

from __future__ import annotations
from pathlib import Path

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
)

from ...loaders.file_registry import registry


class NewFieldMeasurementDialog(QDialog):
    """
    Input dialog for near field measurement data.

    Includes basic data validation.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Add New Near Field Measurement",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)

        # --- Widgets ---
        self.field_type_field = QComboBox()
        self.source_format_field = QComboBox()

        field_types = registry.loaders.keys()
        self.field_type_field.addItems(field_types)

        self._update_source_formats()

        self.field_name_field = QLineEdit(self)
        self.field_name_field.setText("Measured Field")
        self.field_name_field.setPlaceholderText(
            "Enter the name for the field"
        )

        self.path_field = QLineEdit(self)
        self.path_field.setPlaceholderText(
            "Choose or enter the path to the fields file"
        )

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(QIcon.fromTheme("folder-open"))

        self.help_label = QLabel(
            f"Available extensions are: "
            f"{', '.join(self._get_available_extensions())}"
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

        form_layout.addRow("Field Type:", self.field_type_field)
        form_layout.addRow("Source Format:", self.source_format_field)

        form_layout.addRow("Field Name:", self.field_name_field)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_field, 1)
        path_row.addWidget(self.btn_browse, 0)
        form_layout.addRow("Save directory:", path_row)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        form_layout.addRow(self.help_label)

        layout.addWidget(self.buttons)

        # --- Connections ---
        self.field_type_field.currentTextChanged.connect(
            self._update_source_formats
        )
        self.field_type_field.currentTextChanged.connect(
            self._update_help_label
        )
        self.source_format_field.currentTextChanged.connect(
            self._update_help_label
        )

        self.btn_browse.clicked.connect(self._on_browse_clicked)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        self.path_field.returnPressed.connect(self._try_accept)

    # --- Public Methods ---
    def get_info(self) -> dict:
        """Return (name, path) chosen by the user."""
        return {
            "field_type": self.field_type_field.currentText(),
            "source_type": self.source_format_field.currentText(),
            "field_name": self.field_name_field.text(),
            "path": self.path_field.text(),
        }

    # --- Private Methods ---

    def _update_source_formats(self) -> None:
        """Update available source formats based on field type."""
        field_type = self.field_type_field.currentText()
        source_format_types = registry.loaders[field_type].keys()

        # Remove all items before updating items
        for _ in range(self.source_format_field.count()):
            self.source_format_field.removeItem(0)

        self.source_format_field.addItems(source_format_types)

    def _on_browse_clicked(self) -> None:
        """Create folder selection dialog."""
        start_dir = self.path_field.text().strip() or str(Path.home())
        chosen = QFileDialog.getOpenFileName(
            self,
            "Select Fields File",
            start_dir,
            filter=",".join(self._get_available_extensions()),
        )
        if chosen[0]:
            self.path_field.setText(chosen[0])

    def _update_help_label(self) -> None:
        self.help_label.setText(
            f"Available extensions are: "
            f"{', '.join(self._get_available_extensions())}"
        )

    def _get_available_extensions(self) -> list[str]:
        field_type = self.field_type_field.currentText()
        source_type = self.source_format_field.currentText()

        file_extensions = registry.loaders[field_type][source_type]
        return [f"*{extension}" for extension in file_extensions]

    def _is_input_valid(self, silent: bool) -> bool:
        raw_path = self.path_field.text().strip()

        if not raw_path:
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Location",
                    "Please select a fields file.",
                )
            return False

        p = Path(raw_path)

        if not p.exists():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Invalid Location",
                    "The chosen file does not exist.",
                )
            return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()
