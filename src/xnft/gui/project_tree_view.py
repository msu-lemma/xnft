"""
Custom QTreeView subclass to extend context menu actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from PySide6.QtGui import QAction, QIcon, QContextMenuEvent
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QTreeView,
    QMenu,
    QAbstractItemView,
)


from ..project import manager


class ProjectTreeView(QTreeView):
    """Custom QTreeView subclass to extend context menu actions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Allow editing node items
        self.setEditTriggers(
            QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.DoubleClicked
        )

        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)

    def contextMenuEvent(self, ctx_menu_event: QContextMenuEvent) -> None:
        """
        Handle adding context menu (right click) items.

        Context menu actions `context_actions` are added via decorators applied
        to nodes in the xnft/core/project/nodes classes.

        TODO: should implement a more unified framework for adding project
              menu items based on context menu actions. Currently, menu items
              don't automatically populate and this section of could would need
              to be duplicated elsewhere to achieve this.
        """
        # Get node at context menu index
        index = self.indexAt(ctx_menu_event.pos())
        node = index.internalPointer()

        # Get context_actions associated with node
        context_actions = getattr(node, "context_actions", [])
        if not context_actions:  # not all nodes need context actions
            return

        # Build the context menu based on associated actions
        menu = QMenu(self)
        for context_action in context_actions:

            # If context action has an associated icon
            if context_action.icon_name:
                action = QAction(
                    self.model().get_icon(
                        context_action.icon_name, from_theme=True
                    ),
                    context_action.label,
                    menu,
                )

            # Else if no icon
            else:
                action = QAction(
                    context_action.label,
                    menu,
                )

            # Set action enabled or disabled
            action.setEnabled(bool(context_action.enabled))
            if context_action.tooltip:
                action.setToolTip(context_action.tooltip)

            # Add a separator _before_ this item
            if context_action.separator:
                menu.addSeparator()

            # Check special action types, else simply invoke callable
            if context_action.action == "ui_action":
                helper_dialog = context_action.helper_dialog
                invoke_function = context_action.invoke
                # fmt: off
                action.triggered.connect(
                    lambda
                    checked=False,
                    helper_dialog=helper_dialog,
                    target_node=node,
                    invoke_function=invoke_function,
                    main=self.window():
                    main._ui_action(helper_dialog, target_node, invoke_function)
                )
                # fmt: on
            elif context_action.action == "close_project" and isinstance(
                node, manager.Project
            ):
                # fmt: off
                action.triggered.connect(
                    lambda
                    checked=False,
                    model=self.model(),
                    proj=node:
                    model.remove_project(proj)
                )
                # fmt: on
            else:
                # If no context.action specified, directly invoke callable
                invoke = getattr(context_action, "invoke", None)
                if callable(invoke):
                    action.triggered.connect(
                        lambda checked=False, inv=invoke: inv()
                    )
                pass

            menu.addAction(action)

        menu.exec(ctx_menu_event.globalPos())

    def get_active_project(self):
        """
        Get the project associated with the currently selected field.

        Used to get project to apply project-related program menu tasks.
        """
        selected_idx = self.selectedIndexes()
        if not selected_idx:
            return None
        else:
            # Only possible to select one project at a time, so just
            # return project at that index
            selected_idx = selected_idx[0]
        project_node = selected_idx.internalPointer()

        # Find root node (project)
        while not project_node.is_root:
            project_node = project_node.parent

        return project_node
