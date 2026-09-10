"""
Module providing graphical user interfaces.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import importlib.metadata
import logging
import sys
from pathlib import Path

from PySide6.QtCore import (
    QModelIndex,
    QSettings,
    Qt,
    QThread,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QWidget,
)

from ..common.plugins import discover_plugins
from ..loaders import register_builtin_loaders
from ..project import manager
from ..project.io import read_project
from ..project.nodes.project import Project
from ..resources.paths import resource_path
from .dialogs.project.new_project_dialog import NewProjectDialog
from .models.project_tree_model import ProjectManagerTreeModel
from .utils import center_window
from .views.mdi_area import QMdiAreaWatermark
from .views.project_tree_view import ProjectTreeView
from .workers.worker import SpawnWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main Qt window object.
    """

    def __init__(self, project_manager):
        super().__init__()

        self.settings = QSettings()

        self.setWindowTitle(f"xNFT - version {importlib.metadata.version('xnft')}")
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

        # TODO: Handle project action function calls on separate thread helper using signals/slots
        #       similar to _ui_action; unify worker function calling framework

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
        self._file_tool_bar.addAction(self._about_act)
        self.addToolBar(self._file_tool_bar)

    def create_status_bar(self):

        status = self.statusBar()
        status.showMessage("Ready")

        # Add progress bar in container to set margins properly
        progress_container = QWidget()
        progress_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(5, 0, 5, 0)
        progress_layout.setSpacing(0)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 1)
        self.progress.setFixedWidth(350)

        progress_layout.addWidget(self.progress)
        progress_container.setFixedWidth(350 + 5 + 5)
        status.addPermanentWidget(progress_container)

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
        self.properties_table.setColumnWidth(0, 150)

        properties_dock.setWidget(self.properties_table)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, properties_dock)
        self._view_menu.addAction(properties_dock.toggleViewAction())

        selection_model = self.project_tree.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(
                lambda current_index, _: self._node_info_from_index(current_index)
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
            if isinstance(attr, property) and getattr(
                attr.fget, "__gui_property__", False
            ):
                label = attr.fget.__gui_property__["label"]
                order = attr.fget.__gui_property__["order"]
                formatter = attr.fget.__gui_property__["formatter"]

                value = getattr(node, name)
                if formatter:
                    value = formatter(value)

                if value:
                    props.append((order, label, value, name))

        props.sort(key=lambda x: x[0])

        # Populate table
        self.properties_table.setRowCount(len(props))

        for row, (_, label, value, name) in enumerate(props):
            label_item = QTableWidgetItem(label)
            value_item = QTableWidgetItem(str(value))

            for item in (label_item, value_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.properties_table.setItem(row, 0, label_item)
            self.properties_table.setItem(row, 1, value_item)

    def _about(self):
        meta = importlib.metadata.metadata("xnft")

        authors = "\n".join([meta.get("Author"), *meta.get("Author-email").split(", ")])

        QMessageBox.about(
            self,
            "About xNFT",
            f"xNFT Version {meta.get('Version')}\n\n"
            f"{meta.get('Summary')}\n\n"
            "Copyright 2025-2026 The Laboratory for Electromagnetics and mm-Wave Antennas (LEmmA), Electromagnetics Research Group (EMRG), Michigan State University.\n\n"
            f"Authors:\n{authors}\n\n"
            f"License: {meta.get('License')}",
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
            self.statusBar().showMessage(f"New Project Path: {project_path!s}")

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

    def _ui_action(
        self, helper_dialog, target_node, invoke_function, spawn_thread=False
    ):
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

        invoke_kwargs = {}
        run_function = True

        # If a helper dialog is provided, get args and invoke; else invoke without args
        if helper_dialog is not None:
            dialog = helper_dialog(self, target_node=target_node)

            try:
                if dialog.exec() == QDialog.Accepted:
                    invoke_kwargs = dialog.get_selections()
                else:
                    # If the user selects "Cancel", don't run the function
                    run_function = False
            finally:
                # Handle garbage collection on the main gui thread.  Allowing GC to run on the
                # worker thread can cause segfault.
                dialog.deleteLater()
                dialog = None

        if not run_function:
            return

        if spawn_thread:
            thread = QThread(self)
            worker = SpawnWorker(invoke_function, invoke_kwargs)
            worker.moveToThread(thread)

            thread.started.connect(worker.run)

            worker.finished.connect(self._on_invoke_finished)
            worker.error.connect(self._on_invoke_error)

            worker.finished.connect(thread.quit)
            worker.error.connect(thread.quit)

            worker.finished.connect(worker.deleteLater)
            worker.error.connect(worker.deleteLater)

            thread.finished.connect(thread.deleteLater)

            # Retain references while the operation is in progress.
            self._invoke_thread = thread
            self._invoke_worker = worker

            self.statusBar().showMessage(f"{target_node.name}: Working...")
            self.progress.setRange(0, 0)
            self.progress.show()

            thread.start()
        else:
            result_dict = invoke_function(**invoke_kwargs)
            self._on_invoke_finished(result_dict)

    def _on_invoke_finished(self, result_dict):

        if result_dict is None:
            return

        # Reset progress bar to idle
        self.progress.setRange(0, 1)

        status = result_dict.get("status")
        if status:
            self.statusBar().showMessage(status)

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

    def _on_invoke_error(self, exc):
        # Reset progress bar to idle
        self.progress.setRange(0, 1)
        # Disable error for now as "cancel" is not handled properly
        # self.statusBar().showMessage(f"Error: {exc}")

    def restore_all(self):
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


def init_application():
    register_builtin_loaders()
    discover_plugins()

    # TODO/FIXME: for debug only
    import faulthandler

    faulthandler.enable(all_threads=True)


def main():
    """
    Main GUI entrypoint.
    """
    init_application()

    sys.argv[0] = "xNFT"  # Overwrite name of command to show application name

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setWindowIcon(QIcon(str(resource_path("icons", "xnft_flat.png"))))

    app.setApplicationName("xnft")
    app.setApplicationDisplayName("xNFT")
    app.setOrganizationDomain("lemma.msu.edu")
    app.setOrganizationName("LEmmA")

    pm = manager.Manager()
    window = MainWindow(pm)
    window.show()

    exit_code = app.exec()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
