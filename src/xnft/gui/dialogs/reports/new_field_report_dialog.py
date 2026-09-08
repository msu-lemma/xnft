"""
Define new field report dialog window.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ....common.enums import NodeType


class NewFieldReport(QDialog):
    """
    Input dialog for field report.

    Parameters
    ----------
    parent : QWidget | None, optional
        Parent widget for dialog, by default None
    target_node : Node | None, optional
        Target node invoking this dialog, by default None
    show_fields : bool, optional
        Show fields selection in helper, by default True
    select_multiple_fields : bool, optional
        Allow user to select multiple fields in the dialog, by default False
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        target_node=None,
        show_fields=True,
        select_multiple_fields=False,
    ):
        super().__init__(parent)
        self.setWindowTitle("New Field Report")
        self.setMinimumWidth(480)

        self.target_node = target_node
        self.show_fields = show_fields

        # ===== Widgets =====

        # -- Report Name Section --

        group_report_name = QGroupBox()

        group_report_name.setFlat(True)
        self.le_report_name = QLineEdit(self)
        self.le_report_name.setText("Field Report")
        self.le_report_name.setPlaceholderText("Enter the name for the report")

        form_layout_report_name = QFormLayout()
        form_layout_report_name.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout_report_name.addRow("Report Name", self.le_report_name)
        form_layout_report_name.setContentsMargins(0, 0, 0, 0)

        group_report_name.setLayout(form_layout_report_name)

        # -- Data Selection Section --

        self.lw_report_fields = QListWidget()
        if select_multiple_fields:
            self.lw_report_fields.setSelectionMode(QListWidget.ExtendedSelection)

        self._update_field_options()

        # Generate help label based on platform type
        mod_key = "⌘" if platform.system() == "Darwin" else "ctrl"
        label_freq_help = QLabel(
            f"To select multiple fields hold {mod_key} or shift, or {mod_key}-A to select all."
        )
        label_freq_help.setStyleSheet("color: #777")

        form_layout_data = QFormLayout()
        form_layout_data.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        if show_fields:
            form_layout_data.addRow("Report Field:", self.lw_report_fields)
            if select_multiple_fields:
                form_layout_data.addRow(label_freq_help)

        group_data_selection = QGroupBox("Data Source")
        group_data_selection.setLayout(form_layout_data)

        # -- Dialog Butons --

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        # === Top-level layout ===
        layout = QVBoxLayout(self)

        layout.addWidget(group_report_name)
        if show_fields:
            layout.addWidget(group_data_selection)
        # layout.addWidget(group_plot_parameters)

        layout.addWidget(self.buttons)

        # === Connections ===

        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        self.le_report_name.returnPressed.connect(self._try_accept)

        # -- Set current selection row to trigger callbacks --
        self.lw_report_fields.setCurrentRow(0)

    # --- Public Methods ---
    def get_selections(self) -> dict:
        """Return values chosen by the user."""
        output_dict = {}
        output_dict["report_name"] = self.le_report_name.text().strip()
        if self.show_fields:
            output_dict["fields"] = [
                x.data(Qt.UserRole) for x in self.lw_report_fields.selectedItems()
            ]
        return output_dict

    # --- Private Methods ---

    def _update_field_options(self):
        self.lw_report_fields.clear()

        self.fields_node = None
        for tmp_node in self.target_node.parent.children:
            if tmp_node.node_type == NodeType.FIELDS:
                self.fields_node = tmp_node
                break
        assert self.fields_node is not None

        field_options = [
            (f"{x.name}", x)
            for x in self.fields_node.children
            # if x.node_type == self.cb_field_type.currentData()
        ]

        for label, data in field_options:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_report_fields.addItem(item)

    def _is_input_valid(self, silent: bool) -> bool:
        name = self.le_report_name.text().strip()

        if not name:
            if not silent:
                QMessageBox.warning(
                    self, "Missing Name", "Please enter a transform node name."
                )
            return False

        if not self.lw_report_fields.selectedItems():
            if not silent:
                QMessageBox.warning(
                    self,
                    "Missing Field(s)",
                    "Please select at least one field for the report.",
                )
            return False

        return True

    def _try_accept(self) -> None:
        if self._is_input_valid(silent=True):
            self.accept()

    def _on_accept(self) -> None:
        if self._is_input_valid(silent=False):
            self.accept()
