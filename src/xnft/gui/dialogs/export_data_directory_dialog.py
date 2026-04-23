"""
Helper dialog to export data into a folder with various file types.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...project.nodes.fields import FieldNode
    from ...project.nodes.reports import ReportNode


class ExportDataDirectoryDialog(QDialog):
    """
    Dialog for exporting data to disk.

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
        target_node: "FieldNode" | "ReportNode" | None = None,
        help_str: str = ""
    ):
        super().__init__(parent)
        self.setWindowTitle("Export Data to Directory")
        self.setMinimumWidth(540)

        self.target_node = target_node

        # --- Create Widgets ---

        # Create file_entry_row widget for exported data file name
        self.fe_directory_location = FileEntryRow(
            "Choose or enter the directory path to the save the exported data files",
            get_available_extensions=self._get_available_extensions,
            parent=self,
        )

        self.cb_file_type = QComboBox()
        self.cb_file_type.addItems(self._get_available_extensions())

        self.label_file_help = QLabel(help_str)
        self.label_file_help.setWordWrap(True)
        self.label_file_help.setStyleSheet("color: #777")

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Create Layout ---
        self.form_layout = QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.form_layout.addRow("Save Directory:", self.fe_directory_location)
        self.form_layout.addRow("File Type:", self.cb_file_type)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form_layout)
        if help_str != "":
            self.form_layout.addRow(self.label_file_help)

        layout.addWidget(self.buttons)

        # --- Add Connections ---

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        self.fe_directory_location.le_path.returnPressed.connect(self._try_accept)

    def get_selections(self) -> dict:
        """Return values chosen by user."""
        return {
            "directory_path": Path(self.fe_directory_location.le_path.text().strip()),
            "file_type": self.cb_file_type.currentText(),
        }

    def _get_available_extensions(self, glob_format=True) -> list[str]:
        if self.target_node is None:
            return list()
        file_extensions = self.target_node.file_export_types
        if glob_format:
            return [f"*{extension}" for extension in file_extensions]
        else:
            return file_extensions

    def _is_input_valid(self, silent: bool) -> bool:
        directory_path = Path(self.fe_directory_location.le_path.text().strip())

        if directory_path.parent == Path(".") or not directory_path.parent.exists():
            if not silent:
                QMessageBox.warning(self, "Invalid Directory", "Please enter a valid directory path.")
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
        """
        super().__init__(parent)
        self.parent = parent

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.get_available_extensions = get_available_extensions

        self.le_path = QLineEdit(self)
        self.le_path.setPlaceholderText(placeholder)

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(QIcon.fromTheme("folder-open"))

        self._layout.addWidget(self.le_path, 1)
        self._layout.addWidget(self.btn_browse, 0)

        self.btn_browse.clicked.connect(self._on_browse_clicked)

    def _on_browse_clicked(self) -> None:
        """Create folder selection dialog."""
        start_dir = self.le_path.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Select data export destination",
            start_dir
        )

        if chosen:
            self.le_path.setText(chosen)
