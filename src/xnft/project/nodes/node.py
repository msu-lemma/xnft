"""
Base Node classes and actions for Project tree.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

import inspect
import io
import logging
import zipfile
from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar
from uuid import UUID, uuid4

import dill
import h5py
import numpy as np
import xarray as xr

from ...common.enums import NodeType

logger = logging.getLogger(__name__)


# -- Unpickler for Future Code Refactoring --------


class ProjectUnpickler(dill.Unpickler):
    """Custom unpickler that handles class renames and module moves for backward compatibility."""

    ALIASES: ClassVar[dict[tuple[str, str], type]] = {
        # Add class aliases here if classes are renamed or moved in future versions:
        # ("xnft.project.nodes.old_module", "OldNodeName"): NewNodeClass,
    }

    def find_class(self, module: str, name: str) -> Any:
        if (module, name) in self.ALIASES:
            return self.ALIASES[(module, name)]
        return super().find_class(module, name)


# -- GUI Actions --------


@dataclass
class ContextAction:
    """Data class for right-click menu context actions."""

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
    enabled: Callable[[Node], bool] | bool = True,
    tooltip: str | None = None,
    icon_name: str | None = None,
    order: int = 100,
    action: str | None = None,
    helper_dialog: object | None = None,
    separator: bool | None = False,
    spawn_thread: bool | None = False,
):
    """
    Decorator to add a ContextAction (right-click menu item) to a method.

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
    enabled : Callable[["Node"], bool] | bool, optional
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
            "spawn_thread": spawn_thread,
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


# -- Core Node Implementation -------


@dataclass
class Node:
    """Base class for a node in the project hierarchy."""

    # File serialization metadata
    _registry: ClassVar[dict[str, type[Node]]] = {}
    _aliases: ClassVar[dict[str, str]] = {}
    FILE_SCHEMA_VERSION: ClassVar[int] = 1

    # Node values
    id: UUID = field(default_factory=uuid4, init=False)
    name: InitVar[str | None] = None
    node_type: InitVar[NodeType] = NodeType.UNKNOWN
    _name: str | None = field(init=False, default=None)
    _node_type: NodeType = field(init=False, default=NodeType.UNKNOWN)
    name_editable: bool | None = False
    attributes: dict | None = field(default_factory=dict)
    data: Any | None = None
    icon_name: object | None = "text-x-generic"

    # Node traversal pointers
    _parent: Node | None = None
    _children: list[Node] = field(default_factory=list)

    def __init_subclass__(cls, **kwargs):
        """Add subclasses to registry on init."""
        super().__init_subclass__(**kwargs)
        cls._registry[cls.__name__] = cls

    def __post_init__(self, name: str | None, node_type: NodeType, /) -> None:  # ty: ignore[invalid-dataclass]
        self._name = name
        self._node_type = node_type

    # -- Node Property Getter/Setters (GUI) -----------

    @property
    @gui_property(label="Name", order=0)
    def name(self):  # noqa: F811
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    @gui_property(label="Node Type", order=1)
    def node_type(self):  # noqa: F811
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
            raise TypeError(f"Node 'parent' must be of type 'Node' got {type(parent)}.")

    # -- Children ------------

    @property
    def children(self) -> list[Node]:
        """Return list of this node's children."""
        return self._children

    @children.setter
    def children(self, children: list[Node]):
        """Add children from list of Nodes."""
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        """Add a single child Node."""
        if isinstance(child, Node):
            child.parent = self
            self._children.append(child)
        else:
            raise TypeError(f"Node children must be of type 'Node', got {type(child)}.")

    def remove_child(self, child):
        """Remove a single child Node."""
        if not isinstance(child, Node):
            raise TypeError(f"Node children must be of type 'Node', got {type(child)}.")
        if child not in self._children:
            raise ValueError("Attempting to remove item that is not a child of node.")
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
        return not self.parent

    def get_child_by_index(self, index) -> Node:
        """Get a child Node by its index below this node."""
        return self._children[index]

    def index_of_node(self, node: Node) -> int:
        """Get the index of a Node below this node."""
        return self._children.index(node)

    @property
    def root(self) -> Node:
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
        """
        Collect all ContextAction items added by decorator.

        Returns
        -------
        list[ContextAction]
            A list of all ContextActions added via decorators.

        """
        actions: list[ContextAction] = []

        for name, function in inspect.getmembers(
            self.__class__,
            predicate=inspect.isfunction,
        ):
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
                ),
            )

        actions.sort(key=lambda a: a.order)
        return actions

    # -- File Serialization (ZIP Container) ---------------

    def to_zip(self, file_path: str | Path, compression_level: int = 4):
        """Save project to a ZIP container archive (.xnft)."""
        data_store: dict[str, Any] = {}

        def _detach_data(node: Node):
            # Only detach heavy binary arrays/datasets intended for HDF5 storage
            if getattr(node, "data", None) is not None and isinstance(
                node.data, (np.ndarray, xr.Dataset, xr.DataArray)
            ):
                data_store[node.id.hex] = node.data
                node.data = None
            for child in node.children:
                _detach_data(child)

        def _reattach_data(node: Node):
            if node.id.hex in data_store:
                node.data = data_store[node.id.hex]
            for child in node.children:
                _reattach_data(child)

        _detach_data(self)

        try:
            metadata_bytes = dill.dumps(self, protocol=dill.HIGHEST_PROTOCOL)

            h5_buffer = io.BytesIO()
            with h5py.File(h5_buffer, "w") as h5f:
                for node_id, data in data_store.items():
                    group = h5f.create_group(node_id)
                    DataNode._write_h5_data(
                        group, data, compression_level=compression_level
                    )

            with zipfile.ZipFile(
                file_path, "w", compression=zipfile.ZIP_ZSTANDARD
            ) as zf:
                zf.writestr("metadata.pkl", metadata_bytes)
                if data_store:
                    zf.writestr("data.h5", h5_buffer.getvalue())

        finally:
            _reattach_data(self)

    @classmethod
    def from_zip(cls, file_path: str | Path) -> Node:
        """Load project from a ZIP container archive (.xnft)."""
        with zipfile.ZipFile(file_path, "r") as zf:
            metadata_bytes = zf.read("metadata.pkl")
            root_node = ProjectUnpickler(io.BytesIO(metadata_bytes)).load()

            if "data.h5" in zf.namelist():
                h5_bytes = zf.read("data.h5")
                with h5py.File(io.BytesIO(h5_bytes), "r") as h5f:

                    def _load_data(node: Node):
                        if node.id.hex in h5f:
                            node.data = DataNode._read_h5_data(h5f[node.id.hex])
                        for child in node.children:
                            _load_data(child)

                    _load_data(root_node)

        return root_node

    # -- Basic Operations --------

    def __eq__(self, node):
        if not isinstance(node, Node):
            return False
        return self.id == node.id


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
        if source_node is not None and not isinstance(source_node, Node):
            raise TypeError(
                f'Argument "source_node" must be of type {Node} or None got {type(source_node)}',
            )
        self._source = source_node

    # -- File Serialization Overrides ------------

    @staticmethod
    def _write_h5_data(group: h5py.Group, data: Any, compression_level: int = 4):
        """Write array datasets into HDF5 binary group."""
        if data is None:
            return

        if isinstance(data, (xr.Dataset, xr.DataArray)):
            is_da = isinstance(data, xr.DataArray)
            ds = data.to_dataset(name="data") if is_da else data
            group.attrs["_type"] = "xarray"
            group.attrs["_is_da"] = is_da

            group.create_dataset(
                "_attrs",
                data=np.frombuffer(
                    dill.dumps(data.attrs),
                    dtype=np.uint8,
                ),
            )
            group.create_dataset(
                "_data_vars",
                data=np.frombuffer(
                    dill.dumps(list(ds.data_vars.keys())),
                    dtype=np.uint8,
                ),
            )

            for var_name, var in ds.variables.items():
                vg = group.create_group(str(var_name))
                arr = var.values
                kwargs = {}
                if arr.dtype.kind in ("U", "O"):
                    arr = arr.astype(object)
                    kwargs["dtype"] = h5py.string_dtype(encoding="utf-8")
                elif compression_level and arr.size > 0:
                    kwargs["compression"] = "gzip"
                    kwargs["compression_opts"] = compression_level

                vg.create_dataset("values", data=arr, **kwargs)
                vg.create_dataset(
                    "_dims",
                    data=np.frombuffer(
                        dill.dumps(list(var.dims)),
                        dtype=np.uint8,
                    ),
                )
                vg.create_dataset(
                    "_attrs",
                    data=np.frombuffer(
                        dill.dumps(var.attrs),
                        dtype=np.uint8,
                    ),
                )

        elif isinstance(data, np.ndarray):
            group.attrs["_type"] = "numpy"
            kwargs = {}
            if compression_level and data.size > 0:
                kwargs["compression"] = "gzip"
                kwargs["compression_opts"] = compression_level
            group.create_dataset("array", data=data, **kwargs)

    @staticmethod
    def _read_h5_data(group: h5py.Group) -> Any:
        """Read array datasets from HDF5 group."""
        dtype = group.attrs.get("_type")

        if dtype == "xarray":
            is_da = bool(group.attrs.get("_is_da", False))
            xr_attrs = dill.loads(group["_attrs"][:].tobytes())
            data_vars_keys = set(dill.loads(group["_data_vars"][:].tobytes()))

            data_vars, coords = {}, {}
            da_raw = None

            for var_name in group:
                if var_name in ("_attrs", "_data_vars"):
                    continue
                vg = group[var_name]
                arr = vg["values"][:]
                if arr.dtype == object:
                    arr = np.array(
                        [
                            x.decode("utf-8") if isinstance(x, bytes) else str(x)
                            for x in arr.flat
                        ]
                    ).reshape(arr.shape)

                dims = dill.loads(vg["_dims"][:].tobytes())
                vattrs = dill.loads(vg["_attrs"][:].tobytes())

                if is_da and var_name == "data":
                    da_raw = (arr, dims, vattrs)
                elif var_name in data_vars_keys:
                    data_vars[var_name] = xr.DataArray(arr, dims=dims, attrs=vattrs)
                else:
                    coords[var_name] = xr.DataArray(arr, dims=dims, attrs=vattrs)

            if is_da and da_raw is not None:
                arr, dims, vattrs = da_raw
                return xr.DataArray(
                    arr, dims=dims, coords=coords or None, attrs=xr_attrs
                )
            return xr.Dataset(data_vars=data_vars, coords=coords, attrs=xr_attrs)

        elif dtype == "numpy":
            arr = group["array"][:]
            if arr.dtype == object:
                arr = np.array(
                    [
                        x.decode("utf-8") if isinstance(x, bytes) else str(x)
                        for x in arr.flat
                    ]
                ).reshape(arr.shape)
            return arr

        return None
