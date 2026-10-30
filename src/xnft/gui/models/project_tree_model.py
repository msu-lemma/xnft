"""
Custom QAbstractItemModel subclass for managing the ProjecManager interface
to the QTreeView.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from ...project.nodes.node import DataNode, Node
from ...project.nodes.project import Project
from ..utils import get_icon


class ProjectManagerTreeModel(QAbstractItemModel):
    """
    Custom QAbstractItemModel subclass for managing the ProjecManager
    interface to the QTreeView.

    For more information refer to:
    https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractItemModel.html
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)

        self._project_manager = project_manager

    def columnCount(self, parent=None) -> int:
        """Return number of colums. Our model only has one column."""
        if parent is None:
            parent = QModelIndex()
        return 1

    def rowCount(self, parent=None) -> int:
        """
        Return the number of rows under the given parent.

        When the parent is valid it means that rowCount is returning the
        number of children of parent.
        """
        if parent is None:
            parent = QModelIndex()

        # Top-level node is project manager
        if not parent.isValid():
            return self._project_manager.project_count
        # For lower-level nodes, return child_count
        parent_node = parent.internalPointer()
        return parent_node.child_count

    def index(self, row: int, column: int, parent=None) -> QModelIndex:
        """Return QModelIndex at requested location."""
        if parent is None:
            parent = QModelIndex()

        # Top-level node is project manager
        if not parent.isValid():
            if row >= self._project_manager.project_count:
                return QModelIndex()

            proj = self._project_manager.get_project_by_index(row)
            return self.createIndex(row, column, proj)

        parent_node = parent.internalPointer()
        child = parent_node.get_child_by_index(row)
        return self.createIndex(row, column, child)

    def _get_index_for_item(self, item: Node | Project | None) -> QModelIndex:
        """Helper to compute the QModelIndex for any Project or Node."""
        if item is None:
            return QModelIndex()

        if isinstance(item, Project):
            row = self._project_manager.index_of_project(item)
            return self.createIndex(row, 0, item)

        if isinstance(item, Node) and item.parent is not None:
            row = item.parent.children.index(item)
            return self.createIndex(row, 0, item)

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """
        Returns the parent of the model index, or QModelIndex() if it has no parent.

        Get parent of node, then create associated QModelIndex.
        """
        parent_node = index.internalPointer().parent

        if isinstance(parent_node, Project):
            row = self._project_manager.index_of_project(parent_node)
            return self.createIndex(row, 0, parent_node)

        if isinstance(parent_node, Node):
            row = parent_node.parent.children.index(parent_node)
            return self.createIndex(row, 0, parent_node)

        return QModelIndex()

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Returns the data stored under the given `role` for the item referred
        to by the `index`.

        Parameters
        ----------
        index : QModelIndex
            Model index to access data at.
        role : Qt.ItemDataRole, optional
            Role of the model index to access, by default Qt.DisplayRole.

        Returns
        -------
        object
            Data stored in the model index role.

        """
        # Return labels for tree items
        if role in (Qt.DisplayRole, Qt.EditRole):
            node = index.internalPointer()
            if isinstance(node, (DataNode, Project)):
                label = node.name
            else:
                label = node.node_type
            return label

        # Return icons for tree items
        if role == Qt.DecorationRole:
            node = index.internalPointer()
            icon_name = getattr(node, "icon_name", "")

            # If the icon name has a . in it, assume it's a file path,
            # otherwise, assume it's from the theme.
            if "." in icon_name:
                return get_icon(icon_name)
            return get_icon(icon_name, from_theme=True)

        return None

    def insert_project(self, project: Project) -> QModelIndex:
        """
        Insert a top-level project into the project manager tree.

        Parameters
        ----------
        project : project.Project
            Project object to be inserted.

        Returns
        -------
        QModelIndex
            Newly intserted model index.

        """
        parent_index = QModelIndex()

        # Append project to the tree
        insert_row_index = self._project_manager.project_count

        self.beginInsertRows(parent_index, insert_row_index, insert_row_index)
        self._project_manager.add_project(project)
        self.endInsertRows()

        # Return the new model index to caller for other functions to use
        model_index = self.createIndex(insert_row_index, 0, project)

        return model_index

    def remove_project(self, project: Project):
        """
        Remove a top-level project in the project manager tree.

        Should be called when closing a project.

        Parameters
        ----------
        proj : project.Project
            Project to be removed.

        """
        remove_row_index = self._project_manager.index_of_project(project)

        parent_index = QModelIndex()

        self.beginRemoveRows(parent_index, remove_row_index, remove_row_index)
        self._project_manager.remove_project(project)
        self.endRemoveRows()

    def insert_node(self, parent_item: Node, node: Node) -> QModelIndex:
        """
        Insert a node in the project manager tree.

        Parameters
        ----------
        parent_item : project.Node
            Parent of node being inserted.
        node : project.Node
            Node object to insert.

        Returns
        -------
        QModelIndex
            Newly inserted model index.
        """
        parent_index = self._get_index_for_item(parent_item)
        insert_row_index = parent_item.child_count  # append to end

        self.beginInsertRows(parent_index, insert_row_index, insert_row_index)
        parent_item.add_child(node)
        self.endInsertRows()

        model_index = self.createIndex(insert_row_index, 0, node)
        return model_index

    def remove_node(self, parent_or_node: Node, node: Node | None = None):
        """
        Remove a node from the project manager tree and update Qt views.

        Parameters
        ----------
        parent_or_node : project.Node
            The node to remove, OR the parent node if `node` is also explicitly passed.
        node : project.Node, optional
            Node object to remove if parent_or_node was passed as parent.
        """
        if node is not None:
            parent_item = parent_or_node
            target_node = node
        else:
            target_node = parent_or_node
            parent_item = target_node.parent

        if parent_item is None:
            return

        remove_row_index = parent_item.children.index(target_node)
        parent_index = self._get_index_for_item(parent_item)

        self.beginRemoveRows(parent_index, remove_row_index, remove_row_index)
        parent_item.remove_child(target_node)
        self.endRemoveRows()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """
        Returns the item flags for the given index.

        Returns a combination of flags that enables the item (ItemIsEnabled),
        allows it to be selected (ItemIsSelectable), and if specified by the
        Node, allows it to be edited (ItemIsEditable).

        Parameters
        ----------
        index : QModelIndex
            Model index to generate the flags for.

        Returns
        -------
        ItemFlag
            Item flags.

        """
        if not index.isValid():
            return Qt.NoItemFlags

        # Default flags: always enabled and selectable
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        item = index.internalPointer()

        # Enable inline editing for DataNodes and any explicitly editable node
        if isinstance(item, DataNode) or getattr(item, "name_editable", False):
            flags |= Qt.ItemIsEditable

        return flags

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        """
        Sets the `role` data for the item at `index` to `value`.

        The dataChanged() signal should be emitted if the data was
        successfully set.

        Parameters
        ----------
        index : QModelIndex
            Model index to update.
        value : object
            New data to set.
        role : ItemFlag, optional
            Model index role to set data for, by default Qt.EditRole

        Returns
        -------
        bool
            True if successful; otherwise False.

        """
        if role not in (Qt.EditRole, Qt.DisplayRole):
            return False

        if not index.isValid():
            return False

        node = index.internalPointer()
        if not isinstance(node, (DataNode, Project)):
            return False

        # Allow renaming for DataNodes or any node with name_editable=True
        if not (isinstance(node, DataNode) or getattr(node, "name_editable", False)):
            return False

        new_name = str(value).strip()
        if not new_name:
            return False  # Reject empty names

        if new_name != node.name:
            node.name = new_name
            # Emit dataChanged signal so QTreeView redraws the updated name
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])

        return True
