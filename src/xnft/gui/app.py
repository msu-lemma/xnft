"""
Module providing graphical user interfaces.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import html
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

from ..common.plugins import register_plugins
from ..loaders import register_builtin_loaders
from ..project import manager
from ..project.io import read_project
from ..project.nodes.project import Project
from ..resources.paths import resource_path
from .dialogs.project.new_project_dialog import NewProjectDialog
from .models.project_tree_model import ProjectManagerTreeModel
from .tasks.bridge import TaskBridge
from .tasks.worker import SpawnWorker
from .utils import center_window
from .views.mdi_area import QMdiAreaWatermark
from .views.project_tree_view import ProjectTreeView

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main Qt window object."""

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

        # Track active background execution threads
        self._running_threads = set()

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
                lambda current_index, _: self._node_info_from_index(current_index),
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
                attr.fget,
                "__gui_property__",
                False,
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

        author_values = [
            meta.get("Author"),
            *(meta.get("Author-email") or "").split(", "),
        ]
        authors = "<br>".join(html.escape(author) for author in author_values if author)

        raw_project_url_list = meta.get_all("Project-URL")

        if raw_project_url_list:
            project_urls = "<br>".join(
                [
                    f"<b>{x.split(',')[0]}</b>: "
                    f'<a href="{x.split(",", 1)[1].strip()}">{x.split(",", 1)[1].strip()}</a>'
                    for x in raw_project_url_list
                ]
            )
        else:
            project_urls = ""

        msg = QMessageBox(self)
        msg.setWindowTitle("About xNFT")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            f"""
            <p><b>xNFT Version {meta.get("Version")}</b></p>
            <p>{meta.get("Summary")}</p>
            <p>{project_urls}</p>
            <p><b>Authors:</b><br>{authors}</p>
            <p>Copyright 2025-2026 Michigan State University.</p>
            <p><b>License:</b> {meta.get("License-Expression")}</p>
            """
        )
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        msg.exec()

    def create_plot_area(self):
        # Create MDI area for windows to exist
        self.mdi_area = QMdiAreaWatermark()
        self.setCentralWidget(self.mdi_area)

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
        if active_project is None:
            self.statusBar().showMessage("No project selected to save.")
            return

        self._run_async_task(
            func=active_project.save,
            message=f"Saving {active_project.name}...",
            on_finished=lambda status: self.statusBar().showMessage(
                status or "Project saved."
            ),
        )

    def _open_project(self):
        start_dir = str(Path.home())
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            "Select xNFT Project File",
            start_dir,
            filter="*.xnft",
        )
        if not chosen:
            return

        file_path = Path(chosen)

        def _on_load_complete(proj):
            model_index = self.model.insert_project(proj)
            self.project_tree.expandRecursively(model_index)
            self.project_tree.setCurrentIndex(model_index)
            self.project_tree.scrollTo(model_index)
            self.statusBar().showMessage(f"Loaded project '{proj.name}'.")

        self._run_async_task(
            func=read_project,
            args=(file_path,),
            message=f"Loading {file_path.name}...",
            on_finished=_on_load_complete,
        )

    def _set_ui_busy(self, busy: bool, message: str = ""):
        """Lock/unlock UI controls and set progress status."""
        self.menuBar().setEnabled(not busy)
        self._file_tool_bar.setEnabled(not busy)
        self.project_tree.setEnabled(not busy)
        self.properties_table.setEnabled(not busy)
        if self.centralWidget():
            self.centralWidget().setEnabled(not busy)

        if busy:
            self.statusBar().showMessage(message)
            self.progress.setRange(0, 0)
            self.progress.show()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
            self.progress.setRange(0, 1)
            self.progress.setValue(0)

    def _on_task_completed(self, thread):
        """Called on Main Thread when a background task finishes or errors."""
        self._running_threads.discard(thread)
        if not self._running_threads:
            self._set_ui_busy(False)

    def _run_async_task(
        self,
        func,
        args: tuple = (),
        kwargs: dict | None = None,
        message: str = "Processing...",
        on_finished=None,
        on_error=None,
    ):
        """Spawns an async task with safe cross-thread signal dispatching."""
        kwargs = kwargs or {}
        self._set_ui_busy(True, message)

        thread = QThread()
        worker = SpawnWorker(func, invoke_args=args, invoke_kwargs=kwargs)
        worker.moveToThread(thread)

        # Bridge lives on the Main Thread (parented to self)
        bridge = TaskBridge(thread, worker, on_finished, on_error, self)

        worker.finished.connect(bridge.handle_finished)
        worker.error.connect(bridge.handle_error)

        thread._worker = worker
        thread._bridge = bridge
        self._running_threads.add(thread)

        thread.started.connect(worker.run)
        thread.start()
        return thread

    def _ui_action(
        self,
        helper_dialog,
        target_node,
        invoke_function,
        spawn_thread=False,
    ):
        """
        Perform actions that interact with the UI from external models
            (e.g., nodes).

        Examples
        --------
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

        if not run_function:
            return

        if spawn_thread:
            self._run_async_task(
                func=invoke_function,
                kwargs=invoke_kwargs,
                message=f"{target_node.name}: Working...",
                on_finished=self._on_invoke_finished,
                on_error=self._on_invoke_error,
            )
        else:
            result_dict = invoke_function(**invoke_kwargs)
            self._on_invoke_finished(result_dict)

    def _on_invoke_finished(self, result_dict):
        if result_dict is None:
            return

        status = result_dict.get("status")
        if status:
            self.statusBar().showMessage(status)

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

    def _on_invoke_error(self, exc, tb_str=None):
        self.statusBar().showMessage(f"Operation failed: {exc}")

    def restore_all(self):
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def closeEvent(self, event):
        """Prevent crash on close by waiting for running background threads."""
        if self._running_threads:
            reply = QMessageBox.question(
                self,
                "Task in Progress",
                "A save or load operation is currently running.\nWait for it to complete before closing?",
                QMessageBox.StandardButton.Wait | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Wait,
            )

            if reply == QMessageBox.StandardButton.Wait:
                self.statusBar().showMessage(
                    "Waiting for background operations to finish..."
                )
                still_running = False
                for thread in list(self._running_threads):
                    thread.quit()
                    if not thread.wait(3000):
                        still_running = True

                if still_running:
                    QMessageBox.warning(
                        self,
                        "Tasks Still Active",
                        "Background operations could not be stopped immediately. Please try closing again shortly.",
                    )
                    event.ignore()
                    return
            else:
                event.ignore()
                return

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


def init_application():
    register_builtin_loaders()
    register_plugins()


def main():
    """Main GUI entrypoint."""
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
