from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QAction, QIcon, QContextMenuEvent
from PySide6.QtWidgets import (
    QTreeView,
    QMenu,
    QAbstractItemView,
)

from ..core import project


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
        if column < 0 or column >= self.columnCount(parent):
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
            # Top level, no parent
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
        if role == Qt.DecorationRole:
            item = index.internalPointer()
            icon_name = getattr(item, "icon_name", "")
            # If the icon name has a . in it, assume it's a file path,
            # otherwise, assume it's from the theme.
            if "." in icon_name:
                return QIcon(icon_name)
            else:
                return QIcon.fromTheme(icon_name)
        return None

    def insert_project(self, proj: project.Project):
        """Insert a top-level project in the project manager tree.

        Parameters
        ----------
        proj : project.Project
            Project object to be inserted.
        """
        parent_index = QModelIndex()

        # Insert in the last row of the project tree
        insert_row_index = self._project_manager.project_count
        self.beginInsertRows(parent_index, insert_row_index, insert_row_index)

        # Add the new project to the project mnanager
        self._project_manager.add_project(proj)
        self.endInsertRows()

    def remove_project(self, proj: project.Project):
        """Remove a top-level project in the project manager tree.

        Should be called when closing a project.

        Parameters
        ----------
        proj : project.Project
            Project to be removed.
        """
        remove_row_index = self._project_manager.index_of_project(proj)

        parent_index = QModelIndex()

        self.beginRemoveRows(parent_index, remove_row_index, remove_row_index)
        self._project_manager.remove_project(proj)
        self.endRemoveRows()

    def insert_node(self, parent_item: project.Node, node: project.Node):
        """Insert a node in the project manager tree.

        Parameters
        ----------
        parent_item : project.Node
            Parent of node being inserted.
        node : project.Node
            Node object to insert.
        """
        parent_row_index = parent_item.parent.children.index(parent_item)

        parent_index = self.createIndex(parent_row_index, 0, parent_item)
        insert_row_index = parent_item.child_count

        self.beginInsertRows(parent_index, insert_row_index, insert_row_index)
        parent_item.add_child(node)
        self.endInsertRows()

    def remove_node(self, parent_item: project.Node, node: project.Node):
        """Remove a node from the project manager tree.

        Parameters
        ----------
        parent_item : project.Node
            Parent of item being removed.
        node : project.Node
            Node object to remove.
        """
        parent_row_index = parent_item.parent.children.index(parent_item)

        parent_index = self.createIndex(parent_row_index, 0, parent_item)
        remove_row_index = parent_item.child_count

        self.beginRemoveRows(parent_index, remove_row_index, remove_row_index)
        parent_item.remove_child(node)
        self.endRemoveRows()

    def flags(self, index: QModelIndex):
        """Returns the item flags for the given index.

        Teturns a combination of flags that enables the item (ItemIsEnabled),
        allows it to be selected (ItemIsSelectable), and if specified by the
        Node, allows it to be edited (ItemIsEditable).

        Parameters
        ----------
        index : QModelIndex
            _description_

        Returns
        -------
        ItemFlag
            Item flags.
        """
        if not index.isValid():
            return Qt.NoItemFlags

        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        item = index.internalPointer()
        editable = getattr(item, "name_editable", False)
        if editable:
            base |= Qt.ItemIsEditable

        return base

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        """Sets the role data for the item at index to value.

        The dataChanged() signal should be emitted if the data was
        successfully set.

        Parameters
        ----------
        index : QModelIndex
        value : object
        role : ItemFlag, optional
            _description_, by default Qt.EditRole

        Returns
        -------
        bool
            True if successful; otherwise False.
        """
        if not index.isValid():
            return False

        if role not in (Qt.EditRole, Qt.DisplayRole):
            return False

        item = index.internalPointer()
        item_editable = getattr(item, "name_editable", False)

        if not item_editable:
            return False

        if hasattr(item, "name"):
            new_name = str(value)
            if new_name != item.name:
                item.name = new_name

                # Notify the view
                self.dataChanged.emit(
                    index, index, [Qt.DisplayRole, Qt.EditRole]
                )

            return True

        return False


class ProjectTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Allow editing node items
        self.setEditTriggers(
            QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.DoubleClicked
        )

    # Add context menu from decorators
    def contextMenuEvent(self, e: QContextMenuEvent) -> None:
        idx = self.indexAt(e.pos())

        node = idx.internalPointer()
        actions = node.menu_actions

        if not actions:
            return

        menu = QMenu(self)
        for action in actions:
            if action.icon_name:
                qaction = QAction(
                    QIcon.fromTheme(action.icon_name), action.label, menu
                )
            else:
                qaction = QAction(action.label, menu)
            qaction.setEnabled(action.enabled)

            if action.tooltip:
                qaction.setToolTip(action.tooltip)

            qaction.triggered.connect(action.invoke)
            menu.addAction(qaction)

        # If Node is a Project, add special action to close project
        if isinstance(node, project.Project):
            # menu.addSeparator()
            close_action = QAction(
                QIcon.fromTheme("window-close"), "Close Project", menu
            )
            close_action.setStatusTip("Close this project")
            # TODO: add special method for "close project" that will prompt
            # the user to save unsaved changes, if any, before removing
            # fmt: off
            close_action.triggered.connect(
                lambda checked=False,
                model=self.model(),
                proj=node: 
                model.remove_project(proj)
            )
            # fmt: on
            menu.addAction(close_action)

        menu.exec(e.globalPos())

    def get_active_project(self):
        """Get the project associated with the currently selected field."""
        selected_idx = self.selectedIndexes()
        if not selected_idx:
            print("No node selected")
            return None
        else:
            # Only one item may be selected at a time
            selected_idx = selected_idx[0]
        project_node = selected_idx.internalPointer()

        # Find root node (project)
        while not project_node.is_root:
            project_node = project_node.parent

        return project_node
