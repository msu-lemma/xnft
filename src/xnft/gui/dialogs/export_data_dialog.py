"""
Helper dialog to export data to various file types.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from ...project.nodes.fields import FieldNode
    from ...project.nodes.reports import ReportNode
from ...core.enums import (
    FieldType,
)


class ExportDataDialog(QDialog):
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
        target_node: FieldNode | ReportNode | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Export Data to File")
        self.setMinimumWidth(540)

        self.target_node = target_node

        # --- Create Widgets ---

        # Create file_entry_row widget for exported data file name
        self.fe_file_location = FileEntryRow(
            "Choose or enter the path to the save the exported data file",
            get_available_extensions=self._get_available_extensions,
            parent=self,
        )

        self.label_file_help = QLabel(
            f"Available file types are: " f"{', '.join(self._get_available_extensions())}."
        )
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

        self.form_layout.addRow("Save Path:", self.fe_file_location)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form_layout)
        self.form_layout.addRow(self.label_file_help)

        layout.addWidget(self.buttons)

        # --- Add Connections ---

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        self.fe_file_location.le_path.returnPressed.connect(self._try_accept)

    def get_selections(self) -> dict:
        """Return values chosen by user."""
        return {
            "file_path": Path(self.fe_file_location.le_path.text().strip()),
        }

    def _update_help_label(self) -> None:
        self.label_file_help.setText(
            f"Available extensions are: " f"{', '.join(self._get_available_extensions())}"
        )

    def _get_available_extensions(self, glob_format=True) -> list[str]:
        if self.target_node is None:
            return list()
        file_extensions = self.target_node.file_export_types
        if glob_format:
            return [f"*{extension}" for extension in file_extensions]
        else:
            return file_extensions

    def _loaders_info(self, file_registry):
        """
        Return dictionary of field type, source type and accepted file
        extensions and polarizations store in file.
        """
        loader_dict = {
            FieldType.NEAR: defaultdict(list),
            FieldType.FAR: defaultdict(list),
        }

        for key, loader in file_registry._loaders.items():
            attr_dict = loader.__attributes__
            source = attr_dict["source"]
            field = attr_dict["field"]
            extension = attr_dict["extension"]
            loader_dict[field][source].append(extension)

        return loader_dict

    def _is_input_valid(self, silent: bool) -> bool:
        file_path = Path(self.fe_file_location.le_path.text().strip())
        file_type = file_path.suffix

        if file_path.parent == Path(".") or not file_path.parent.exists():
            if not silent:
                QMessageBox.warning(self, "Invalid File Path", "Please enter a valid file path.")
            return False

        extension_list = self._get_available_extensions(glob_format=False)

        if file_type not in extension_list:
            if not silent:
                QMessageBox.warning(
                    self,
                    "Invalid File Type",
                    f"Please enter a valid file extension. "
                    f"Available options are {', '.join(extension_list)}",
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
        chosen = QFileDialog.getSaveFileName(
            self,
            "Select data export destination",
            start_dir,
            filter=" ".join(self.get_available_extensions()),
        )
        if chosen[0]:
            self.le_path.setText(chosen[0])
