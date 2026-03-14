"""
Handle xnft fields actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass, InitVar
from typing import Optional
import logging

from ...gui.dialogs.fields.new_field_measurement_dialog import (
    NewFieldMeasurementDialog,
)
from ...loaders.file_registry import file_registry
from .node import Node, DataNode, NodeType, context_action, gui_property
from .coordinates import CoordinateNode

from ...core.enums import CoordinateSystemType, FieldType, DataSourceType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class FieldsNode(Node):
    icon_name: str = "src/xnft/resources/icons/fields.svg"

    def __post_init__(self, name: Optional[str] = None, node_type: NodeType = NodeType.UNKNOWN):
        super().__post_init__(name, node_type)

        self._node_type = NodeType.FIELDS
        self._name = NodeType.FIELDS

    @context_action(
        "New Measured Field",
        order=10,
        enabled=True,
        icon_name="document-new",
        action="ui_action",
        helper_dialog=NewFieldMeasurementDialog,
    )
    def new_measured_field(self, field_type, source_type, field_name, file_info_list):

        # Read measured field file
        field_data = file_registry.load(
            source=source_type, field=field_type, file_list=file_info_list
        )

        # Add pointer to coordinates (All measured data should have intrinsic
        # coordinates associated with it)
        coordinates_node = None
        for tmp_node in self.parent.children:
            if tmp_node.node_type == NodeType.COORDINATES:
                coordinates_node = tmp_node
                break

        coordinate_data = field_data.coords
        coordinate_node = CoordinateNode(
            name=f"{field_name} Coordinates",
            data=coordinate_data,
            coordinate_type=(  # TODO: Add better detection of coordinate system
                CoordinateSystemType.CARTESIAN
                if field_type == FieldType.NEAR
                else CoordinateSystemType.SPHERICAL
            ),
            source=None
        )

        field_node = FieldNode(
            name=field_name,
            source_type=source_type,
            attributes={"path": file_info_list},
            icon_name="text-x-generic",
            data=field_data,
            field_type=field_type,
            coordinates_node=coordinate_node
        )

        # field_node.coordinates = coordinate_node
        coordinate_node.source = field_node

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
class FieldNode(DataNode):
    coordinates_node: InitVar[Optional[CoordinateNode | None]] = None
    field_type: InitVar[Optional[FieldType]] = FieldType.UNKNOWN
    source_type: InitVar[Optional[DataSourceType | None]] = DataSourceType.UNKNOWN
    source: InitVar[Optional[Node]] = None


    name_editable: Optional[bool] = True


    def __post_init__(
            self, 
            name: Optional[str] = None, 
            node_type: Optional[NodeType] = NodeType.UNKNOWN,
            source: Optional[Node | None] = None,
            coordinates_node: Optional[CoordinateNode | None] = None,
            field_type: Optional[FieldType] = FieldType.UNKNOWN,
            source_type: Optional[DataSourceType] = DataSourceType.UNKNOWN,
        ):
        node_type = NodeType.FIELDS
        self.coordinates_node = coordinates_node
        self.field_type = field_type
        self.source_type = source_type

        super().__post_init__(name=name, node_type=node_type, source=source)

    @property
    @gui_property(label='Coordinates', order=5, formatter=lambda x: x.name)
    def coordinates_node(self):
        return self._coordinates_node
    
    @coordinates_node.setter
    def coordinates_node(self, coords_node):
        self._coordinates_node = coords_node

    @property
    @gui_property(label='Field Type', order=3)
    def field_type(self):
        return self._field_type
    
    @field_type.setter
    def field_type(self, field_type):
        self._field_type = field_type

    @property
    @gui_property(label='Source Type', order=5)
    def source_type(self):
        return self._source_type
    
    @source_type.setter
    def source_type(self, source_type):
        self._source_type = source_type

    @property
    def display_type(self):
        # return (
        #     f"{'Measured ' if self.source_type else ''}{str(self.node_type).title()}"
        # )
        return f"{self.source_type}"
