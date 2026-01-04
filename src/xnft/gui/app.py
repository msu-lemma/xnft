"""Module providing graphical user interfaces."""

import sys
from pathlib import Path
import pyqtgraph as pg

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import (
    QAction,
    QIcon,
    QKeySequence,
    QWindow,
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
)

import logging.config

from .. import __version__
from ..core import project
from .dialogs.new_project_dialog import NewProjectDialog
from .project_tree_model import ProjectManagerTreeModel, ProjectTreeView

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main Qt window object.
    """

    def __init__(self, project_manager):
        super().__init__()
        self.setWindowTitle(f"xNFT - version {__version__}")
        self.project_manager = project_manager

        self._text_edit = QTextEdit()

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()
        self.create_project_manager_widget(self.project_manager)
        self.create_plot_area()

    def create_actions(self):
        # -- Create new project --

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
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._quit_act)

        # Placeholder Menus
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._project_menu = self.menuBar().addMenu("&Project")
        self._view_menu = self.menuBar().addMenu("&View")

        self._help_menu = self.menuBar().addMenu("&Help")
        self._help_menu.addAction(self._about_act)

    def create_tool_bars(self):
        self._file_tool_bar = self.addToolBar("File")
        self._file_tool_bar.addAction(self._new_project_act)
        self._file_tool_bar.addAction(self._save_act)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def create_project_manager_widget(self, pm):
        dock = QDockWidget("Project Manager", self)

        self.model = ProjectManagerTreeModel(pm)
        self.project_tree = ProjectTreeView()
        self.project_tree.setModel(self.model)
        self.project_tree.setAlternatingRowColors(True)
        self.project_tree.setUniformRowHeights(True)
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setIndentation(15)
        self.project_tree.expandAll()

        dock.setWidget(self.project_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._view_menu.addAction(dock.toggleViewAction())

    def _about(self):
        QMessageBox.about(self, "About xNFT", f"xNFT Version {__version__}")

    def create_plot_area(self):

        # Create MDI area for windows to exist
        area = QMdiArea()
        self.setCentralWidget(area)

        self.pw = pg.PlotWidget()
        self.win = QMdiSubWindow()
        self.win.setWidget(self.pw)
        self.win.setWindowTitle("Plot Window 1")

        area.addSubWindow(self.win)

    def _new_project(self):
        dialog = NewProjectDialog(self, title="New Project")
        if dialog.exec() == QDialog.Accepted:
            name, path = dialog.get_project_info()
            project_path = Path(path) / f"{name}.xnft"
            self.statusBar().showMessage(
                f"New Project Path: {str(project_path)}"
            )

            # Create the underlying project object
            new_project = project.Project(name=name, path=project_path)
            self.model.insert_project(new_project)

            # Find the newly added project in the project tree
            new_project_row_index = (
                self.model._project_manager.index_of_project(new_project)
            )
            model_index = self.model.index(
                new_project_row_index, 0, QModelIndex()
            )

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
    # app.setStyle("Fusion")
    pm = project.Manager()
    pm.add_project(
        project.Project(
            name="TestProject", path=Path.home() / "TestProject.xnft"
        )
    )

    window = MainWindow(pm)
    center_window(window, target_size_ratio=0.7)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
