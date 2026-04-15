"""
Handle xnft fields actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging
from pathlib import Path


from ...gui.dialogs.fields.new_field_measurement_dialog import NewFieldMeasurementDialog
from ...gui.dialogs.export_data_dialog import ExportDataDialog
from ...loaders.file_registry import file_registry
from .node import Node, DataNode, NodeType, context_action, gui_property
from .coordinates import CoordinateNode

from ...core.enums import CoordinateSystemType, FieldType, DataSourceType
from ...core.data_writers import write_dataset_hdf5

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
            source=None,
        )

        field_node = FieldNode(
            name=field_name,
            source_type=source_type,
            attributes={"path": file_info_list},
            icon_name="text-x-generic",
            data=field_data,
            field_type=field_type,
            coordinates_node=coordinate_node,
        )

        # field_node.coordinates = coordinate_node
        coordinate_node.source = field_node

        status = f"Successfully created {field_type.lower()} node."

        node_pair_list = [
            (self, field_node),
            (coordinates_node, coordinate_node),
        ]

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict


@dataclass(kw_only=True)
class FieldNode(DataNode):
    _coordinates_node: CoordinateNode | None = field(default=None, init=False, repr=False)
    _field_type: FieldType = field(default=FieldType.UNKNOWN, init=False)
    _source_type: DataSourceType = field(default=DataSourceType.UNKNOWN, init=False)

    name_editable: Optional[bool] = True
    file_export_types = [".h5", ".csv"]

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        source: Optional[Node] = None,
        coordinates_node: Optional[CoordinateNode] = None,
        field_type: FieldType = FieldType.UNKNOWN,
        source_type: DataSourceType = DataSourceType.UNKNOWN,
        **kwargs,
    ):
        super().__init__(
            name=name,
            node_type=NodeType.FIELDS,
            source=source,
            **kwargs,
        )

        self.coordinates_node = coordinates_node
        self.field_type = field_type
        self.source_type = source_type

    @property
    @gui_property(label="Coordinates", order=5, formatter=lambda x: x.name)
    def coordinates_node(self):
        return self._coordinates_node

    @coordinates_node.setter
    def coordinates_node(self, coords_node):
        self._coordinates_node = coords_node

    @property
    @gui_property(label="Field Type", order=3)
    def field_type(self):
        return self._field_type

    @field_type.setter
    def field_type(self, field_type):
        self._field_type = field_type

    @property
    @gui_property(label="Source Type", order=5)
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

    @context_action(
        label="Export Field",
        enabled=True,
        tooltip="Write field data to file",
        icon_name="document-save",
        order=100,
        separator=True,
        action="ui_action",
        helper_dialog=ExportDataDialog,
    )
    def export_data(self, file_path: Path):
        if self.data is None:
            return None

        file_type = file_path.suffix

        if file_type == ".h5":
            write_dataset_hdf5(self.data, file_path)

        elif file_type == ".csv":
            self.data.to_dataframe().to_csv(file_path)
        else:
            raise NotImplementedError(
                f"File extention type of {file_type} is not implemented. "
                f"Available options are {', '.join(self.file_export_types)}"
            )
