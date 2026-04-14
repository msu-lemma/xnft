"""
Common helper dialog widgets/layouts.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from pathlib import Path
from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QFileDialog,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QListWidget
)

from ...core.enums import SParameterType


class ListWidgetTitle(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.name = label
        self.label = QLabel(label)
        self.lw = QListWidget()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lw)


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
        for idx, sp_type in enumerate(SParameterType):
            self.cb_sp.addItem(sp_type.value, (sp_type,))
            if sp_type == SParameterType.S21:
                s21_idx = idx

        # Set default type
        self.cb_sp.setCurrentIndex(s21_idx)

        self.btn_browse = QPushButton(self)
        self.btn_browse.setIcon(QIcon.fromTheme("folder-open"))

        self._layout.addWidget(self.le_path, 1)
        self._layout.addWidget(self.cb_sp, 0)
        self._layout.addWidget(self.btn_browse, 0)

        self.btn_browse.clicked.connect(self._on_browse_clicked)
        self.le_path.textChanged.connect(self._on_le_path_update)

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

    def _on_le_path_update(self) -> None:
        """Update SP field."""
        field_type = self.parent.selected_field
        source_format = self.parent.selected_source_format

        extension = Path(self.le_path.text()).suffix

        try:
            loader = file_registry.get_loader(source_format, field_type, extension)
            self.show_sp = loader.__attributes__["has_sp"]
        except Exception:
            pass

    @property
    def show_sp(self):
        return self._show_sp

    @show_sp.setter
    def show_sp(self, show):
        self._show_sp = show
        self.cb_sp.setHidden(not show)