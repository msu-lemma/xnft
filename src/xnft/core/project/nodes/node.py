"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from uuid import uuid4
import inspect
import logging
from ...types import NodeType


logger = logging.getLogger(__name__)


# --- Action metadata + decorator ---
@dataclass
class ContextAction:
    """A structured data class for right-click menu context ctions"""

    label: str
    invoke: Callable[[], None]
    enabled: bool = True
    tooltip: Optional[str] = None
    icon_name: Optional[str] = None
    action: Optional[str] = None
    helper_dialog: Optional[object] = None
    order: int = 100
    separator: bool = False


def context_action(
    label: str,
    enabled: Callable[["Node"], bool] | bool = True,
    tooltip: Optional[str] = None,
    icon_name: Optional[str] = None,
    order: int = 100,
    action: Optional[str] = None,
    helper_dialog: Optional[object | None] = None,
    separator: Optional[bool] = False,
):
    """Decorator to add a ContextAction (right-click menu item) to a method.

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
        Type of special action to be performed
    helper_dialog : QDialog, optional
        Helper dialog to input data for function to be invoked, by default None
    separator : bool, optional
        Add a separator before this item, by default False
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
        }
        return func

    return decorator


# === Project Nodes ===


@dataclass
class Node:
    """Base class for a node in the project hierarchy."""

    # Node values
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "None"
    type: NodeType = NodeType.UNKNOWN
    name_editable: Optional[bool] = False
    attributes: Optional[dict] = field(default_factory=dict)
    data: Optional[object] = None
    icon_name: Optional[object] = "text-x-generic"

    # Node traversal pointers
    _parent: Optional["Node"] = None
    _children: List["Node"] = field(default_factory=list)

    # -- Parents --

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if isinstance(parent, Node):
            self._parent = parent
        else:
            raise TypeError(
                f"Node 'parent' must be of type 'Node'" f" got {type(parent)}."
            )

    # -- Children --

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        # Check type of children
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        if isinstance(child, Node):
            child.parent = self
            self._children.append(child)
        else:
            raise TypeError(
                f"Node children must be of type 'Node'," f" got {type(child)}."
            )

    def remove_child(self, child):
        if not isinstance(child, Node):
            raise TypeError(
                f"Node children must be of type 'Node'," f" got {type(child)}."
            )
        if child not in self._children:
            raise ValueError(
                "Attempting to remove item that is not a child of " "node."
            )
        self._children.remove(child)

    @property
    def child_count(self):
        return len(self._children)

    # -- Node properties --

    @property
    def is_leaf(self):
        return len(self._children) == 0

    @property
    def is_root(self):
        return False if self.parent else True

    def get_child_by_index(self, index):
        return self._children[index]

    def index_of_node(self, node: "Node"):
        return self._children.index(node)

    @property
    def root(self):
        root = self
        while not root.is_root:
            root = root.parent
        return root

    @property
    def display_type(self):
        return self.type

    # -- Menu actions --

    @property
    def context_actions(self) -> list[ContextAction]:
        """Collect all ContextAction items added by decorator.

        Returns
        -------
        list[ContextAction]
            A list of all ContextActions added via decorators.
        """
        actions: list[ContextAction] = []

        for name, function in inspect.getmembers(
            self.__class__, predicate=inspect.isfunction
        ):
            # Check if __context_action__ attribute is available before
            # continuing
            if name == "context_actions":
                continue

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
                )
            )

        # Sort by order then label
        actions.sort(key=lambda a: (a.order, a.label))
        return actions


@dataclass(kw_only=True)
class LeafNode(Node):
    """
    Specialization of Node class with default helper context/helper functions
    unique to leaf nodes.
    """
    # @context_action()
    def edit(self):
        pass

    # @context_action()
    def delete(self):
        pass
    