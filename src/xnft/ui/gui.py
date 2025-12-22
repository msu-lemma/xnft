"""Module providing graphical user interfaces."""

import sys
import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import (
    Qt,
    QFile,
    QAbstractItemModel,
    QModelIndex,
    QPersistentModelIndex,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QPushButton,
    QListWidget,
    QDialog,
    QFileDialog,
    QMessageBox,
    QDockWidget,
    QMdiSubWindow,
    QMdiArea,
    QTextEdit,
    QWidget,
    QTreeView,
)

from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.console import ConsoleWidget

from .. import __version__
from ..core import project, core


class MainWindow(QMainWindow):
    """
    Main Qt window object.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"xnft - version {__version__}")

        self._text_edit = QTextEdit()

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()
        self.create_dock_windows()
        self.create_plot_area()

    def create_actions(self):
        # -- Create new project --
        new_project_icon = QIcon.fromTheme("document-new")
        self._new_project_act = QAction(
            new_project_icon,
            "&New Project...",
            self,
            shortcut=QKeySequence.StandardKey.New,
            statusTip="Create a new project",
            triggered=None,
        )

        icon = QIcon.fromTheme("document-save")
        self._save_act = QAction(
            icon,
            "&Save...",
            self,
            shortcut=QKeySequence.StandardKey.Save,
            statusTip="Save the current form letter",
            triggered=None,
        )

        self._quit_act = QAction(
            "&Quit",
            self,
            shortcut="Ctrl+Q",
            statusTip="Quit the application",
            triggered=self.close,
        )

        self._about_act = QAction(
            icon,
            "&About",
            self,
            statusTip="Application information",
            triggered=self._about,
        )

    def create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._new_project_act)
        self._file_menu.addAction(self._save_act)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._quit_act)

        self._edit_menu = self.menuBar().addMenu("&Edit")

        self._view_menu = self.menuBar().addMenu("&View")

        self._help_menu = self.menuBar().addMenu("&Help")
        self._help_menu.addAction(self._about_act)

    def create_tool_bars(self):
        self._file_tool_bar = self.addToolBar("File")
        self._file_tool_bar.addAction(self._new_project_act)
        self._file_tool_bar.addAction(self._save_act)

        self._edit_tool_bar = self.addToolBar("Edit")

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def create_dock_windows(self):
        dock = QDockWidget("Project Manager", self)

        self.pm = project.Manager()

        self.p1 = project.Project(name="Test Project")

        self.root_a = project.Node(name="root_a", data="value b")
        self.root_b = project.Node(name="root_b", data="value b")

        self.child_a1 = project.Node(name="child_a1", data="value a1")
        self.child_a2 = project.Node(name="child_a2", data="value a2")
        self.child_b1 = project.Node(name="child_b1", data="value b1")

        self.pm.add_project(self.p1)
        self.p1.add_child(self.root_a)
        self.p1.add_child(self.root_b)
        self.root_a.add_child(self.child_a1)
        self.root_a.add_child(self.child_a2)
        self.root_b.add_child(self.child_b1)

        self.model = ProjectManagerTreeModel(self.pm)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.expandAll()

        dock.setWidget(self.tree_view)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._view_menu.addAction(dock.toggleViewAction())

    def _about(self):
        QMessageBox.about(self, "About xNFT", f"xNFT Version {__version__}")

    def create_plot_area(self):

        # Create MDI area for windows to exist
        area = QMdiArea()
        self.setCentralWidget(area)

        # # Create MDI Subwindows
        # subwindow = QMdiSubWindow()
        # subwindow.setWindowTitle("Plotting Window")
        # self._plot = pg.PlotWidget()
        # self._plot.plot(np.random.normal(size=100))
        # subwindow.setWidget(self._plot)
        # area.addSubWindow(subwindow)


class ProjectManagerTreeModel(QAbstractItemModel):
    """
    Class for managing the ProjecManager interface to the QTreeView.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._project_manager = project_manager

    def columnCount(self, parent=QModelIndex()) -> int:
        return 1

    def rowCount(self, parent=QModelIndex()) -> int:
        if not parent.isValid():
            # Top level project
            return self._project_manager.project_count

        parent_item = parent.internalPointer()
        if isinstance(parent_item, project.Project):
            return parent_item.child_count
        elif isinstance(parent_item, project.Node):
            return parent_item.child_count

        return 0

    def index(self, row, column, parent=QModelIndex()) -> QModelIndex:
        if column < 0 or column >= self.columnCount(parent):  # or row < 0:
            return QModelIndex()

        # Project manager node
        if not parent.isValid():
            if row >= self._project_manager.project_count:
                return QModelIndex()
            proj = self._project_manager.get_project_by_index(row)
            return self.createIndex(row, column, proj)

        parent_item = parent.internalPointer()
        if isinstance(parent_item, project.Project):
            if row >= parent_item.child_count:
                return QModelIndex()
            node = parent_item.get_child_by_index(row)
            return self.createIndex(row, column, node)

        elif isinstance(parent_item, project.Node):
            if row >= parent_item.child_count:
                return QModelIndex()
            child = parent_item.get_child_by_index(row)
            return self.createIndex(row, column, child)

        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        if isinstance(item, project.Project):
            # Top level, no parent in view
            return QModelIndex()

        if isinstance(item, project.Node):
            parent_obj = item.parent
            if isinstance(parent_obj, project.Project):
                row = self._project_manager.index_of_project(parent_obj)
                return self.createIndex(row, 0, parent_obj)
            elif isinstance(parent_obj, project.Node):
                grand_parent = parent_obj.parent
                if isinstance(grand_parent, project.Project):
                    row = grand_parent.index_of_node(parent_obj)
                else:
                    row = grand_parent.children.index(parent_obj)
                return self.createIndex(row, 0, parent_obj)

        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            item = index.internalPointer()
            return getattr(item, "name", "")
        return None


def main():
    """
    Main GUI entrypoint.
    """
    app = QApplication(sys.argv)
    # app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
