"""
Base Node classes and actions for Project tree.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import inspect
import logging
from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from enum import StrEnum
from typing import Any, Optional
from uuid import UUID, uuid4

from ...core.enums import NodeType

logger = logging.getLogger(__name__)


@dataclass
class ContextAction:
    """A structured data class for right-click menu context ctions."""

    label: str
    invoke: Callable[[], None]
    enabled: bool = True
    tooltip: str | None = None
    icon_name: str | None = None
    action: str | None = None
    helper_dialog: object | None = None
    order: int = 100
    separator: bool = False
    spawn_thread: bool = False


def context_action(
    label: str,
    enabled: Callable[["Node"], bool] | bool = True,
    tooltip: str | None = None,
    icon_name: str | None = None,
    order: int = 100,
    action: str | None = None,
    helper_dialog: object | None = None,
    separator: bool | None = False,
    spawn_thread: bool | None = False,
):
    """Decorator to add a ContextAction (right-click menu item) to a method.

    For further details on implementation, see xnft/gui/project_tree_view.py
    where a QAction is constructed using these parameters, or xnft/gui/main.py
    where the QAction is executed.

    TODO: Create a more uniform method of handling context actions that unifies
          the processing location to a single file and handles both right-click
          menus as well as window menus.

    Parameters
    ----------
    label : str
        Context menu label
    enabled : Callable[[&quot;Node&quot;], bool] | bool, optional
        Whether or not to enable the context menu action, by default True
    tooltip : Optional[str], optional
        Tooltip message shown on hover, by default None
    icon_name : Optional[str], optional
        Icon to display in context menu, by default None
    order : int, optional
        Value to set order displayed in context menu (lowest first),
        by default 100
    action : str, optional
        Type of special action to be performed. Available actions are:
            `ui_action`, `close_project`
            TODO: these seem somewhat specific; consider generalizing this
                  somehow to avoid special actions.
    helper_dialog : QDialog, optional
        Helper dialog to input data for function to be invoked, by default None
    separator : bool, optional
        Add a separator _before_ this item, by default False
    spawn_thread : bool, optional
        Spawn function in separate worker thread off main GUI thread.  Recommended for non-GUI operations.
    """

    def decorator(func):
        func.__context_action__ = {
            "label": label,
            "enabled": enabled,
            "tooltip": tooltip,
            "icon_name": icon_name,
            "order": order,
            "action": action,
            "helper_dialog": helper_dialog,
            "separator": separator,
            "spawn_thread": spawn_thread
        }
        return func

    return decorator


def gui_property(label=None, order=0, tooltip=None, formatter=None, button=False):
    def decorator(func):
        func.__gui_property__ = {
            "label": label or func.__name__.replace("_", " ").title(),
            "order": order,
            "tooltip": tooltip,
            "formatter": formatter,
            "button": button,
        }
        return func

    return decorator


@dataclass
class Node:
    """Base class for a node in the project hierarchy."""

    # Node values
    id: UUID = uuid4()
    name: InitVar[str | None] = None
    node_type: InitVar[NodeType | None] = NodeType.UNKNOWN
    name_editable: bool | None = False
    attributes: dict | None = field(default_factory=dict)
    data: Any | None = None
    icon_name: object | None = "text-x-generic"

    # Node traversal pointers
    _parent: Optional["Node"] = None
    _children: list["Node"] = field(default_factory=list)

    def __post_init__(self, name: str | None = None, node_type: NodeType = NodeType.UNKNOWN):
        self._name = name
        self._node_type = node_type

    # -- Node Property Getter/Setters (GUI) -----------

    @property
    @gui_property(label="Name", order=0)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    @gui_property(label="Node Type", order=1)
    def node_type(self):
        return self._node_type

    @node_type.setter
    def node_type(self, node_type):
        self._node_type = node_type

    # -- Parents ------------

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if isinstance(parent, Node):
            self._parent = parent
        else:
            raise TypeError(f"Node 'parent' must be of type 'Node'" f" got {type(parent)}.")

    # -- Children ------------

    @property
    def children(self) -> list["Node"]:
        """Return list of this node's children."""
        return self._children

    @children.setter
    def children(self, children: list["Node"]):
        """Add children from list of Nodes."""
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        """Add a single child Node."""
        if isinstance(child, Node):
            child.parent = self
            self._children.append(child)
        else:
            raise TypeError(f"Node children must be of type 'Node'," f" got {type(child)}.")

    def remove_child(self, child):
        """Remove a single child Node."""
        if not isinstance(child, Node):
            raise TypeError(f"Node children must be of type 'Node'," f" got {type(child)}.")
        if child not in self._children:
            raise ValueError("Attempting to remove item that is not a child of " "node.")
        self._children.remove(child)

    @property
    def child_count(self) -> int:
        """Return the number of this node's children."""
        return len(self._children)

    # -- Node properties --------

    @property
    def is_leaf(self) -> bool:
        """Return if this node is a leaf (has no children)."""
        return len(self._children) == 0

    @property
    def is_root(self) -> bool:
        """Return if this node is a root (has no parent)."""
        return False if self.parent else True

    def get_child_by_index(self, index) -> "Node":
        """Get a child Node by its index below this node."""
        return self._children[index]

    def index_of_node(self, node: "Node") -> int:
        """Get the index of a Node below this node."""
        return self._children.index(node)

    @property
    def root(self) -> "Node":
        """Return the root Node above this node."""
        root = self
        while not root.is_root:
            root = root.parent
        return root

    @property
    def display_type(self) -> StrEnum:
        """Return display type of node."""
        return self._node_type

    # -- Context Menu Actions -------------

    @property
    def context_actions(self) -> list[ContextAction]:
        """Collect all ContextAction items added by decorator.

        Returns
        -------
        list[ContextAction]
            A list of all ContextActions added via decorators.
        """
        actions: list[ContextAction] = []

        for name, function in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            meta = getattr(function, "__context_action__", None)
            if not meta:
                continue

            bound_method = getattr(self, name)

            actions.append(
                ContextAction(
                    label=meta["label"],
                    invoke=bound_method,
                    enabled=meta["enabled"],
                    tooltip=meta["tooltip"],
                    icon_name=meta["icon_name"],
                    order=meta["order"],
                    action=meta["action"],
                    helper_dialog=meta["helper_dialog"],
                    separator=meta["separator"],
                    spawn_thread=meta["spawn_thread"],
                )
            )

        # Sort by order provided
        actions.sort(key=lambda a: a.order)
        return actions

    # -- Basic Actions ----------------

    def __eq__(self, node):
        return self.id == node.id


# @dataclass(kw_only=True)
# class DataNode(Node):
#     """
#     Specialization of Node class with default helper context/helper functions
#     unique to leaf nodes.
#     """

#     source: InitVar[Optional[Node]] = None

#     def __post_init__(
#             self,
#             name: Optional[str] = None,
#             node_type: Optional[NodeType] = NodeType.UNKNOWN,
#             source: Optional[Node | None] = None,
#         ):
#         super().__post_init__(name=name, node_type=node_type)

#         self.source = source


@dataclass(kw_only=True, eq=False)
class DataNode(Node):
    _source: Node | None = field(default=None, init=False)

    def __init__(self, *, source=None, name=None, node_type=NodeType.UNKNOWN, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._node_type = node_type
        self.source = source

        if hasattr(type(self), "icon_name"):
            self.icon_name = type(self).icon_name

    @property
    @gui_property(label="Source Node", order=3, formatter=lambda x: x.name if x else "")
    def source(self):
        return self._source

    @source.setter
    def source(self, source_node: Node | None):
        if source_node is not None and not isinstance(source_node, (Node)):
            raise TypeError(
                f'Argument "source_node" must be of type {Node} or None got {type(source_node)}'
            )
        # logger.debug(f"{source_node=}")
        self._source = source_node

    @context_action(
        label="Edit",
        icon_name="mail-message-new",
        enabled=False,
        order=1000,
        separator=True,
    )
    def edit(self):
        pass

    @context_action(
        label="Rename",
        icon_name="format-text-strikethrough",
        enabled=False,
        order=1001,
    )
    def rename(self):
        pass

    @context_action(
        label="Delete",
        icon_name="edit-delete",
        enabled=False,
        order=1002,
        action="ui_action",
    )
    def delete(self):
        pass
