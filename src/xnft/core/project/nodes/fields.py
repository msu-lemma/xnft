"""
Handle xnft project actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass
from typing import Optional
import logging

from ....gui.dialogs.fields.new_field_measurement_dialog import (
    NewFieldMeasurementDialog,
)
from ....loaders.file_registry import registry
from .node import Node, LeafNode, NodeType, context_action
from .coordinates import CoordinateNode

from ...types import CoordinateSystem, FieldType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class FieldsNode(Node):
    name: str = "Fields"
    icon_name: str = "src/xnft/resources/icons/fields.svg"
    type: NodeType = NodeType.FIELDS

    @context_action(
        "New Measured Field",
        order=10,
        enabled=True,
        icon_name="document-new",
        action="ui_action",
        helper_dialog=NewFieldMeasurementDialog,
    )
    def new_measured_field(self, field_type, source_type, field_name, path):

        # Read measured field file
        field_data = registry.load(
            source=source_type, field=field_type, path=path
        )

        field_node = FieldNode(
            name=field_name,
            source_type=source_type,
            measured=True,
            attributes={"path": path},
            icon_name="text-x-generic",
            data=field_data,
            type=field_type,
        )

        # Add pointer to coordinates (All measured data should have intrinsic
        # coordinates associated with it)
        coordinates_node = None
        for tmp_node in self.parent.children:
            if tmp_node.name == "Coordinates":
                coordinates_node = tmp_node
                break
        assert coordinates_node is not None

        coordinate_data = field_data.coords
        coordinate_node = CoordinateNode(
            name=f"{field_name} Coordinates",
            source=field_node,
            data=coordinate_data,
            type=(  # TODO: Add better detection of coordinate system
                CoordinateSystem.CARTESIAN
                if field_type == FieldType.NEAR
                else CoordinateSystem.SPHERICAL
            ),
        )
        # coordinates_node.add_child(coordinate_node)

        field_node.coordinates = coordinate_node

        status = f"Successfully created {field_type.lower()} node."

        node_pair_list = [
            (self, field_node),
            (coordinates_node, coordinate_node),
        ]

        result_dict = {
            "status": status,
            "nodes": node_pair_list
        }

        return result_dict


@dataclass(kw_only=True)
class FieldNode(LeafNode):
    source_type: str
    measured: Optional[bool] = False
    coordinates: Optional[Node] = None
    name_editable: Optional[bool] = True

    @property
    def display_type(self):
        return (
            f"{'Measured ' if self.measured else ''}{str(self.type).title()}"
        )
