"""
Module providing graphical user interfaces.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import sys
from pathlib import Path
import pyqtgraph as pg

from PySide6 import QtGui

from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QSize,
    QRect,
    QRectF,
    QSizeF,
    QPointF,
    QSettings,
    QCoreApplication,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
    QKeySequence,
    QWindow,
    QPainter,
    QPixmap,
    QImage,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QMessageBox,
    QDockWidget,
    QMdiSubWindow,
    QMdiArea,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QToolBar,
)

import logging
import importlib.metadata


from .. import __version__
from ..project import manager
from ..project.nodes.project import Project
from ..project.project_io import read_project

from .dialogs.project.new_project_dialog import NewProjectDialog
from .project_tree_model import ProjectManagerTreeModel
from .project_tree_view import ProjectTreeView
from .mdi_area import QMdiAreaWatermark

# Registers all loaders
import xnft.loaders  # noqa: F401  # pylint: disable=unused-import

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main Qt window object.
    """

    def __init__(self, project_manager):
        super().__init__()

        QCoreApplication.setOrganizationName(
            "LEmmA, Electromagnetics Research Group, Michigan State University"
        )
        QCoreApplication.setOrganizationDomain("engineering.msu.edu")
        QCoreApplication.setApplicationName("xNFT")
        self.settings = QSettings()

        self.setWindowTitle(f"xNFT - version {__version__}")
        self.project_manager = project_manager

        self._text_edit = QTextEdit()

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()
        self.create_project_manager_widgets(self.project_manager)
        self.create_plot_area()

        center_window(self, target_size_ratio=0.7)
        self.restore_all()

    def create_actions(self):


        self._new_project_act = QAction(
            QIcon.fromTheme("document-new"),
            "&New Project...",
            self,
            shortcut=QKeySequence.StandardKey.New,
            statusTip="Create a new project",
            triggered=self._new_project,
        )

        self._save_act = QAction(
            QIcon.fromTheme("document-save"),
            "&Save Project...",
            self,
            shortcut=QKeySequence.StandardKey.Save,
            statusTip="Save the current project",
            triggered=self._save_project,
        )

        self._open_act = QAction(
            QIcon.fromTheme("document-open"),
            "&Open Project...",
            self,
            shortcut=QKeySequence.StandardKey.Open,
            statusTip="Open an existing project",
            triggered=self._open_project,
        )

        self._quit_act = QAction(
            QIcon.fromTheme("application-exit"),
            "&Quit",
            self,
            shortcut="Ctrl+Q",
            statusTip="Quit xNFT",
            triggered=self.close,
        )

        self._about_act = QAction(
            QIcon.fromTheme("help-about"),
            "&About",
            self,
            statusTip="xNFT information",
            triggered=self._about,
        )

    def create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._new_project_act)
        self._file_menu.addAction(self._save_act)
        self._file_menu.addAction(self._open_act)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._quit_act)

        # Placeholder Menus
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._project_menu = self.menuBar().addMenu("&Project")
        self._view_menu = self.menuBar().addMenu("&View")

        self._help_menu = self.menuBar().addMenu("&Help")
        self._help_menu.addAction(self._about_act)

    def create_tool_bars(self):
        self._file_tool_bar = QToolBar("File")
        self._file_tool_bar.setObjectName("ToolbarFile")
        self._file_tool_bar.addAction(self._new_project_act)
        self._file_tool_bar.addAction(self._save_act)
        self._file_tool_bar.addAction(self._open_act)
        self.addToolBar(self._file_tool_bar)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def create_project_manager_widgets(self, pm):

        # == Create project manager tree ==

        pm_dock = QDockWidget("Project Manager", self)
        pm_dock.setObjectName("DockProjectManager")  # Used for restore

        self.model = ProjectManagerTreeModel(pm)
        self.project_tree = ProjectTreeView()
        self.project_tree.setModel(self.model)
        self.project_tree.setAlternatingRowColors(True)
        self.project_tree.setIndentation(15)
        self.project_tree.expandAll()

        pm_dock.setWidget(self.project_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, pm_dock)
        self._view_menu.addAction(pm_dock.toggleViewAction())

        # == Create node info table ==
        # TODO: update to QTableWidget subclass in separate file to pull out custom logic from main gui
        
        properties_dock = QDockWidget("Properties", self)
        properties_dock.setObjectName("DockProperties")  # Used for restore

        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(2)
        self.properties_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.properties_table.verticalHeader().setVisible(False)
        self.properties_table.setAlternatingRowColors(True)
        self.properties_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.properties_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.properties_table.setSelectionMode(QTableWidget.SingleSelection)
        self.properties_table.horizontalHeader().setStretchLastSection(True)

        properties_dock.setWidget(self.properties_table)
        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, properties_dock
        )
        self._view_menu.addAction(properties_dock.toggleViewAction())

        selection_model = self.project_tree.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(
                lambda current_index, _: self._node_info_from_index(
                    current_index
                )
            )

    def _node_info_from_index(self, index: QModelIndex):
        # TODO/FIXME: REVISE
        node = index.internalPointer()
        if node is None:
            self.properties_table.setRowCount(0)
            return

        # Filter by decorator properties
        props = []
        for name in dir(node.__class__):
            attr = getattr(node.__class__, name, None)
            # NOTE: fget is the getter of a property
            if isinstance(attr, property) and getattr(attr.fget, "__gui_property__", False):
                label = attr.fget.__gui_property__['label']
                order = attr.fget.__gui_property__['order']
                formatter = attr.fget.__gui_property__['formatter']
                button = attr.fget.__gui_property__['button']

                value = getattr(node, name)
                if formatter:
                    value = formatter(value)

                props.append((order, label, value, name, button))

        props.sort(key=lambda x: x[0])

        # Populate table
        self.properties_table.setRowCount(len(props))

        for row, (_, label, value, name, button) in enumerate(props):
            label_item = QTableWidgetItem(label)
            value_item = QTableWidgetItem(str(value))

            for item in (label_item, value_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.properties_table.setItem(row, 0, label_item)
            self.properties_table.setItem(row, 1, value_item)

            if button:
                btn = QPushButton("Edit…")
                btn.clicked.connect(lambda _, n=node, field=name: self.open_edit_dialog(n, field))
                self.properties_table.setCellWidget(row, 2, btn)

    def _about(self):
        meta = importlib.metadata.metadata("xnft")

        authors = "\n".join(
            [meta.get("Author"), *meta.get("Author-email").split(", ")]
        )

        QMessageBox.about(
            self,
            "About xNFT",
            f"xNFT Version {__version__}\n\n"
            f"{meta.get("Summary")}\n\n"
            "Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.\n\n"
            f"Authors:\n{authors}",
        )

    def create_plot_area(self):
        # Create MDI area for windows to exist
        self.mdi_area = QMdiAreaWatermark()
        self.setCentralWidget(self.mdi_area)

    def _open_project(self):
        start_dir = str(Path.home())
        chosen = QFileDialog.getOpenFileName(
            self,
            "Select xNFT Project File",
            start_dir,
            filter="*.xnft",
        )

        # Open the project and intsert into tree
        proj = read_project(chosen[0])
        model_index = self.model.insert_project(proj)

        # Expand rows in tree and highlight
        self.project_tree.expandRecursively(model_index)
        self.project_tree.setCurrentIndex(model_index)
        self.project_tree.scrollTo(model_index)

    def _new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, path = dialog.get_project_info()
            project_path = Path(path) / f"{name}.xnft"
            self.statusBar().showMessage(
                f"New Project Path: {str(project_path)}"
            )

            # Create the underlying project object
            new_project = Project(name=name, _path=project_path)
            model_index = self.model.insert_project(new_project)

            # Expand rows in tree and highlight
            self.project_tree.expand(model_index)
            self.project_tree.setCurrentIndex(model_index)
            self.project_tree.scrollTo(model_index)

    def _save_project(self):
        active_project = self.project_tree.get_active_project()
        if active_project is not None:
            save_status = active_project.save()
            self.statusBar().showMessage(save_status)
        else:
            self.statusBar().showMessage("No project selected to save.")

    def _ui_action(self, helper_dialog, target_node, invoke_function):
        """Perform actions that interact with the UI from external models
            (e.g., nodes).
        Examples:
            - add child node to "target_node"
            - create window in MDI area

        Parameters
        ----------
        helper_dialog : QDialog
            Dialog window for data entry.
        target_node : project.Node
            Node to add child to.
        invoke_function : Callable
            A function to callback from the project to perform project action.
        """

        result_dict = None

        # If a helper dialog is provided, get args and invoke; else invoke without args
        if helper_dialog is not None:
            dialog = helper_dialog(self, target_node=target_node)
            if dialog.exec() == QDialog.Accepted:
                invoke_kwargs = dialog.get_selections()

                # Call bound function with kwargs returned from helper_dialog
                result_dict = invoke_function(**invoke_kwargs)

        else:
            result_dict = invoke_function()

        # TODO: handle long-running asynchronous tasks
        # will reqiure callbacks when tasks finish to perform further
        # UI actions
        #
        # tasks = result_dict["tasks"]

        if result_dict is None:
            return

        # Set status bar text
        status = result_dict.get("status", None)
        if status:
            self.statusBar().showMessage(status)

        # Add nodes to project manager tree
        node_pair_list = result_dict.get("nodes", None)
        if node_pair_list:
            model_index = None
            for idx, node_pair in enumerate(node_pair_list):
                parent_node = node_pair[0]
                node = node_pair[1]
                index = self.model.insert_node(parent_node, node)
                self.project_tree.expand(index)
                self.project_tree.setCurrentIndex(index)
                self.project_tree.scrollTo(index)

                # Keep the first node and select this in the tree
                # Other nodes are secondary (e.g., derived nodes that
                # the user did not directly request)
                if idx == 0:
                    model_index = index

            # Expand rows in tree and highlight
            self.project_tree.expand(model_index)
            self.project_tree.setCurrentIndex(model_index)
            self.project_tree.scrollTo(model_index)

        # Add windows to MDI area
        windows = result_dict.get("windows", None)
        if windows:
            for win in windows:
                sub = self.mdi_area.addSubWindow(win)
                sub.show()

    def restore_all(self):
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


def center_window(window: QWindow, target_size_ratio: float = 0.7):
    """Center and resize the window to fill a fraction of the display.

    Parameters
    ----------
    window : QWindow
        Window to be resized
    target_size_ratio : float, optional
        Fraction of the display to resize the window to, by default 0.7
    """
    # Get window geometry
    screen = window.screen()

    # If the screen is available proceed with resizing
    if screen:
        available_geometry = screen.availableGeometry()

        # Set to xx% or min size, whichever is larger
        target_size_ratio = 0.7
        target_width = int(available_geometry.width() * target_size_ratio)
        target_height = int(available_geometry.height() * target_size_ratio)

        min_width = 640  # px
        min_height = 480  # px

        width = max(target_width, min_width)
        height = max(target_height, min_height)

        window.resize(width, height)

        # Center the window
        x = available_geometry.x() + (available_geometry.width() - width) // 2
        y = (
            available_geometry.y()
            + (available_geometry.height() - height) // 2
        )

        window.move(x, y)


def main():
    """
    Main GUI entrypoint.
    """
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    pm = manager.Manager()
    window = MainWindow(pm)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
