# new_project_dialog.py
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
)

from datetime import datetime


class NewProjectDialog(QDialog):
    """
    Input dialog for project name and path.

    Includes basic data validation.
    """

    def __init__(
        self, parent: QWidget | None = None, title: str = "Create New Project"
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)

        # --- Widgets ---
        self.name_field = QLineEdit(self)
        self.name_field.setPlaceholderText("Enter project name")

        self.name_field.setText(
            f"Project_{datetime.today().strftime("%Y%m%d_%H%M%S")}"
        )

        self.path_field = QLineEdit(self)
        self.path_field.setPlaceholderText("Choose or enter a save directory")
        self.path_field.setText(str(Path.home()))

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(QIcon.fromTheme("folder-open"))

        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.addRow("Project name:", self.name_field)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_field, 1)
        path_row.addWidget(self.btn_browse, 0)
        form_layout.addRow("Save directory:", path_row)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)

        layout.addWidget(self.buttons)

        # --- Connections ---
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        self.name_field.returnPressed.connect(self._try_accept)
        self.path_field.returnPressed.connect(self._try_accept)

    # --- Public Methods ---
    def get_project_info(self) -> tuple[str, str]:
        """Return (name, path) chosen by the user."""
        return self.name_field.text().strip(), self.path_field.text().strip()

    # --- Private Methods ---
    def _on_browse_clicked(self) -> None:
        """Create folder selection dialog."""
        start_dir = self.path_field.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            start_dir,
            options=QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            self.path_field.setText(chosen)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.name_field.text().strip()
        raw_path = self.path_field.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a project name."
                )
            return False

        if not raw_path:
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Location",
                    "Please select a project location.",
                )
            return False

        p = Path(raw_path)

        if not p.exists():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Invalid Location",
                    "The chosen directory does not exist.",
                )
            return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()
