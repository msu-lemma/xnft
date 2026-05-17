"""
Define new field measurement dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.

TODO:
    - Add S-param. detection for .h5 files (show S-aram. list next to selected file)
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
)

from ....loaders.file_registry import file_registry
from ....project.nodes.node import Node
from ....core.enums import (
    FieldType,
    DataPolarizationType,
    SParameterType,
    DataSourceType,
    PolarizationType,
)
from ....core.types import FileInfo


class NewFieldMeasurementDialog(QDialog):
    """
    Input dialog for field measurement data.


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
        self.setWindowTitle("New Field Measurement")
        self.setMinimumWidth(540)

        # --- Create Widgets ---
        self.cb_field_type = QComboBox()
        self.cb_source_format = QComboBox()
        self.cb_data_polarization = QComboBox()

        field_types = self._loaders_info(file_registry).keys()
        for idx, field_type in enumerate(field_types):
            # NOTE: Qt casts StrEnum to plain str which breaks some things;
            #       we'll wrap this in a tuple here to mitigate this behavior
            self.cb_field_type.addItem(field_type.value, (field_type,))

        self._update_source_file_formats()

        self.field_name_field = QLineEdit(self)
        self.field_name_field.setText("Measured Field")
        self.field_name_field.setPlaceholderText("Enter the name for the field")

        # Create file_entry_row widgets for data polarization options
        self.fe_combined = FileEntryRow(
            "Choose or enter the path to the field file",
            get_available_extensions=self._get_available_extensions,
            parent=self,
        )
        self.fe_co_pol = FileEntryRow(
            "Choose or enter the path to the co-polarized field file",
            get_available_extensions=self._get_available_extensions,
            parent=self,
        )
        self.fe_cx_pol = FileEntryRow(
            "Choose or enter the path to the cross-polarized field file",
            get_available_extensions=self._get_available_extensions,
            parent=self,
        )

        self.label_file_help = QLabel(
            f"Available extensions are: " f"{', '.join(self._get_available_extensions())}"
        )
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

        self.form_layout.addRow("Field Name:", self.field_name_field)

        self.form_layout.addRow("Field Type:", self.cb_field_type)
        self.form_layout.addRow("Source File Format:", self.cb_source_format)
        self.form_layout.addRow("Source File Polarizations:", self.cb_data_polarization)

        self.form_layout.addRow("Source File:", self.fe_combined)
        self.form_layout.addRow("Source File Co-Pol:", self.fe_co_pol)
        self.form_layout.addRow("Source File Cross-Pol:", self.fe_cx_pol)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form_layout)
        self.form_layout.addRow(self.label_file_help)

        self._update_source_polarization_formats()
        self._update_file_fields_shown()

        layout.addWidget(self.buttons)

        # --- Add Connections ---
        self.cb_field_type.currentTextChanged.connect(self._update_source_file_formats)
        self.cb_field_type.currentTextChanged.connect(self._update_help_label)
        self.cb_source_format.currentTextChanged.connect(self._update_help_label)

        self.cb_source_format.currentTextChanged.connect(self._update_source_polarization_formats)

        self.cb_data_polarization.currentTextChanged.connect(self._update_file_fields_shown)

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        # Enter key creates if valid
        # self.path_field.returnPressed.connect(self._try_accept)

    def get_selections(self) -> dict:
        """Return values chosen by user."""
        data_polarization = self.cb_data_polarization.currentData()[0]

        if data_polarization == DataPolarizationType.COMBO_POL:
            file_info_list = [
                FileInfo(
                    path=Path(self.fe_combined.le_path.text().strip()),
                    polarization={PolarizationType.CO_POL, PolarizationType.CROSS_POL},
                    s_parameters=set(self.fe_combined.cb_sp.currentData()),
                )
            ]
        else:
            co_pol_path = self.fe_co_pol.le_path.text().strip()
            cross_pol_path = self.fe_cx_pol.le_path.text().strip()
            file_info_list = []
            if co_pol_path:
                file_info_list.append(
                    FileInfo(
                        path=Path(co_pol_path),
                        polarization=PolarizationType.CO_POL,
                        s_parameters=set(self.fe_co_pol.cb_sp.currentData()),
                    )
                )
            if cross_pol_path:
                file_info_list.append(
                    FileInfo(
                        path=Path(cross_pol_path),
                        polarization=PolarizationType.CROSS_POL,
                        s_parameters=set(self.fe_cx_pol.cb_sp.currentData()),
                    )
                )

        return {
            "field_type": self.cb_field_type.currentText().strip(),
            "source_type": self.cb_source_format.currentText().strip(),
            "field_name": self.field_name_field.text().strip(),
            "file_info_list": file_info_list,
        }

    @property
    def selected_field(self) -> FieldType:
        return self.cb_field_type.currentData()[0]

    @property
    def selected_source_format(self) -> DataSourceType:
        return self.cb_source_format.currentData()[0]

    def _update_source_file_formats(self) -> None:
        """Update available source file formats based on field type."""
        field_type = self.cb_field_type.currentText()
        source_format_types = self._loaders_info(file_registry)[field_type].keys()

        # Remove all items before updating items
        for _ in range(self.cb_source_format.count()):
            self.cb_source_format.removeItem(0)

        for source_format_type in source_format_types:
            # NOTE: Qt casts StrEnum to plain str which breaks some things;
            #       we'll wrap this in a tuple here to mitigate this behavior
            self.cb_source_format.addItem(source_format_type.value, (source_format_type,))

    def _update_source_polarization_formats(self) -> None:
        """Update available source polarization formats based on source file type."""
        field_type = self.cb_field_type.currentData()[0]
        source_type = self.cb_source_format.currentData()[0]
        loaders = file_registry._loaders

        # Get data polarizations available for source and field type files
        polarization_formats = []
        for key, loader in loaders.items():
            attributes = getattr(loader, "__attributes__")
            if attributes["source"] == source_type and attributes["field"] == field_type:
                polarization_formats.append(attributes["data_polarization"])

        # Remove all items before updating items
        for _ in range(self.cb_data_polarization.count()):
            self.cb_data_polarization.removeItem(0)

        for polarization_format in polarization_formats:
            # NOTE: Qt casts StrEnum to plain str which breaks some things;
            #       we'll wrap this in a tuple here to mitigate this behavior
            self.cb_data_polarization.addItem(polarization_format.value, (polarization_format,))

    def _update_file_fields_shown(self):
        # Enable/disable data polarization specific data selection boxes
        data_polarization = self.cb_data_polarization.currentData()
        if data_polarization is not None:
            data_polarization = data_polarization[0]
        else:
            return

        if data_polarization == DataPolarizationType.COMBO_POL:
            self.form_layout.setRowVisible(self.fe_combined, True)
            self.form_layout.setRowVisible(self.fe_co_pol, False)
            self.form_layout.setRowVisible(self.fe_cx_pol, False)
        else:
            self.form_layout.setRowVisible(self.fe_combined, False)
            self.form_layout.setRowVisible(self.fe_co_pol, True)
            self.form_layout.setRowVisible(self.fe_cx_pol, True)

    def _update_help_label(self) -> None:
        self.label_file_help.setText(
            f"Available extensions are: " f"{', '.join(self._get_available_extensions())}"
        )

    def _get_available_extensions(self, glob_format=True) -> list[str]:
        field_type = self.cb_field_type.currentText()
        source_type = self.cb_source_format.currentText()

        file_extensions = self._loaders_info(file_registry)[field_type][source_type]
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
        name = self.field_name_field.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(self, "Missing Name", "Please enter a field node name.")
            return False

        # TODO: re-implement file path testing to handle FileEntryRow (maybe inside the class)

        # if not raw_path:
        #     if not silent:
        #         QMessageBox.warning(
        #             self,
        #             "Missing Location",
        #             "Please select a field file.",
        #         )
        #     return False

        # p = Path(raw_path)

        # if not p.exists():
        #     if not silent:
        #         QMessageBox.warning(
        #             self,
        #             "Invalid Location",
        #             "The chosen file does not exist.",
        #         )
        #     return False

        # if p.suffix not in self._get_available_extensions(glob_format=False):
        #     if not silent:
        #         field_type = self.cb_field_type.currentText()
        #         source_type = self.cb_source_format.currentText()
        #         extensions = self._get_available_extensions()
        #         QMessageBox.warning(
        #             self,
        #             "Invalid File Type",
        #             "The chosen file does not have a supported file extension."
        #             f"\nValid types for {source_type} {field_type} are: "
        #             f"{', '.join(extensions)}",
        #         )
        #     return False

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
