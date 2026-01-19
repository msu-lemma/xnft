"""
Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""
from PySide6.QtGui import QAction, QIcon, QContextMenuEvent
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QTreeView,
    QMenu,
    QAbstractItemView,
)


from ..core.project import manager


class ProjectTreeView(QTreeView):
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
        """Add context menu (right click) items."""
        idx = self.indexAt(ctx_menu_event.pos())
        if not idx.isValid():
            return

        node = idx.internalPointer()
        menu_actions = getattr(node, "menu_actions", [])
        if not menu_actions:
            return

        menu = QMenu(self)
        for menu_action in menu_actions:
            if menu_action.icon_name:
                action = QAction(
                    self.model.get_icon(menu_action.icon_name, from_theme=True),
                    menu_action.label,
                    menu,
                )
            else:
                action = QAction(
                    menu_action.label,
                    menu,
                )
            action.setEnabled(bool(menu_action.enabled))
            if menu_action.tooltip:
                action.setToolTip(menu_action.tooltip)

            if menu_action.separator:
                menu.addSeparator()

            # Check special action types, else simply invoke callable
            if menu_action.action == "new_node":
                helper_dialog = menu_action.helper_dialog
                invoke_function = menu_action.invoke
                # fmt: off
                action.triggered.connect(
                    lambda
                    checked=False,
                    helper_dialog=helper_dialog,
                    target_node=node,
                    invoke_function=invoke_function,
                    main=self.window():
                    main._new_node(helper_dialog, target_node, invoke_function)
                )
                # fmt: on
            elif menu_action.action == "close_project" and isinstance(
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
                # Fallback for direct callable
                invoke = getattr(menu_action, "invoke", None)
                if callable(invoke):
                    action.triggered.connect(
                        lambda checked=False, inv=invoke: inv()
                    )

            menu.addAction(action)

        if isinstance(node, manager.Project):
            close_action = QAction(
                self.model.get_icon("window-close", from_theme=True), "Close Project", menu
            )
            close_action.setStatusTip("Close this project")
            # fmt: off
            close_action.triggered.connect(
                lambda checked=False,
                model=self.model(),
                proj=node:
                model.remove_project(proj)
            )
            # fmt: on
            menu.addAction(close_action)

        menu.exec(ctx_menu_event.globalPos())

    def get_active_project(self):
        """Get the project associated with the currently selected field."""
        selected_idx = self.selectedIndexes()
        if not selected_idx:
            return None
        else:
            # Only one item may be selected at a time
            selected_idx = selected_idx[0]
        project_node = selected_idx.internalPointer()

        # Find root node (project)
        while not project_node.is_root:
            project_node = project_node.parent

        return project_node
