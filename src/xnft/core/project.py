"""
Handle xnft project actions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from uuid import uuid4
from pathlib import Path
import inspect
import logging.config

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
    order: int = 100


def menu_action(
    label: str,
    enabled: Callable[["Node"], bool] | bool = True,
    tooltip: Optional[str] = None,
    icon_name: Optional[str] = None,
    order: int = 100,
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
    """

    def decorator(func):
        func.__menu_action__ = {
            "label": label,
            "enabled": enabled,
            "tooltip": tooltip,
            "icon_name": icon_name,
            "order": order,
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
    name_editable: bool = False
    attributes: Optional[dict] = field(default_factory=dict)
    data: Optional[object] = None
    icon_name: Optional[object] = "folder"

    # Node traversal pointers
    _parent: Optional["Node"] = None
    _children: List["Node"] = field(default_factory=list)

    # -- Parents --

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if isinstance(parent, (Node, Project)):
            self._parent = parent
        else:
            raise TypeError(
                f"Node 'parent' must be of type 'Node' or 'Project',"
                f" got {type(parent)}."
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

    # -- Menu actions --

    @property
    def menu_actions(self) -> list[ContextAction]:
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
            # Check if __menu_action__ attribute is available before
            # continuing
            if name == "menu_actions":
                continue

            meta = getattr(function, "__menu_action__", None)
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
                )
            )

        # Sort by order then label
        actions.sort(key=lambda a: (a.order, a.label))
        return actions


@dataclass(kw_only=True)
class Fields(Node):
    name: str = "Fields"
    icon_name: str = "src/xnft/resources/icons/fields.svg"

    @menu_action("New Measured Near Field", order=10, enabled=False)
    def new_measured_near_field(self):
        logger.warning("New measured near-field is not yet implemented.")

    @menu_action("New Measured Far Field", order=20, enabled=False)
    def new_measured_far_field(self):
        logger.warning("New measured far-field is not yet implemented.")


@dataclass(kw_only=True)
class Analyses(Node):
    name: str = "Analyses"
    icon_name: str = "src/xnft/resources/icons/function.svg"

    @menu_action(
        "New Planar Near-to-far Field Transform", order=10, enabled=False
    )
    def new_planar_nft(self):
        logger.warning("Near-to-far Field Transform is not yet implemented.")

    @menu_action(
        "New Spherical Near-to-far Field Transform", order=20, enabled=False
    )
    def new_spherical_nft(self):
        logger.warning("Near-to-far Field Transform is not yet implemented.")

    @menu_action("New Near Field Interpolation", order=30, enabled=False)
    def new_near_field_interpolation(self):
        logger.warning("Near field interpolation is not yet implemented.")

    @menu_action("New Far Field Interpolation", order=40, enabled=False)
    def new_far_field_interpolation(self):
        logger.warning("Far field interpolation is not yet implemented.")


@dataclass(kw_only=True)
class Results(Node):
    name: str = "Results"
    icon_name: str = "src/xnft/resources/icons/plot.svg"

    @menu_action("New Near Field Report", order=10, enabled=False)
    def new_near_field_report(self):
        logger.warning("Near field report is not yet implemented.")

    @menu_action("New Far Field Report", order=20, enabled=False)
    def new_far_field_report(self):
        logger.warning("Near field report is not yet implemented.")

    @menu_action("New Antenna Parameters Report", order=30, enabled=False)
    def new_antenna_parameters_report(self):
        logger.warning("Antenna parametes report is not yet implemented.")


@dataclass(kw_only=True)
class Coordinates(Node):
    name: str = "Coordinates"
    icon_name: str = "src/xnft/resources/icons/coordinates.svg"

    @menu_action("New Measurement Coordinates", order=10, enabled=False)
    def new_measurement_coordinates(self):
        logger.warning("New measurement coordinates is not yet implemented.")


@dataclass(kw_only=True)
class Model(Node):
    name: str = "Model"
    icon_name: str = "src/xnft/resources/icons/model.svg"

    @menu_action("New Model Asset", order=10, enabled=False)
    def new_measurement_coordinates(self):
        logger.warning("New model asset is not yet implemented.")


@dataclass(kw_only=True)
class Project(Node):
    path: Optional[Path] = None
    version: int = 1

    def __post_init__(self):
        # Add default project nodes
        self.add_child(Fields(data="value b"))
        self.add_child(Analyses(data="value b"))
        self.add_child(Results(data="value b"))
        self.add_child(Coordinates(data="value b"))
        self.add_child(Model(data="value b"))

        # Allow projects to be renamed in the Project Manager
        self.name_editable = True

    @menu_action(
        "Save Project", order=10, enabled=True, icon_name="document-save"
    )
    def save(self, path=None):
        if path is not None:
            self.path = path
        logger.warning("Project saving not yet implemented.")
        return f"Failed to save {self.name} to path: {self.path}"


# === Project Manager ===


class Manager:
    def __init__(self):
        self._projects: List[Project] = []

    @property
    def projects(self):
        return self._projects

    def add_project(self, project: Project):
        self._projects.append(project)

    def remove_project(self, project: Project):
        self._projects.remove(project)

    @property
    def project_count(self):
        return len(self._projects)

    def get_project_by_index(self, index):
        return self._projects[index]

    def index_of_project(self, project: Project):
        return self._projects.index(project)
