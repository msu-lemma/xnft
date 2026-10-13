"""
Handle xnft fields actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from quantiphy import Quantity

from ...common.enums import CoordinateSystemType, FieldType
from ...common.registry import registry
from ...common.types import DataSource
from ...gui.dialogs.export_data_dialog import ExportDataDialog
from ...gui.dialogs.fields.new_field_measurement_dialog import NewFieldMeasurementDialog
from ...reports.data_writers import write_dataset_hdf5
from .coordinates import CoordinateNode
from .node import DataNode, Node, NodeType, context_action, gui_property

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class FieldsNode(Node):
    icon_name: str = "src/xnft/resources/icons/fields.svg"

    def __post_init__(self, name: str | None, node_type: NodeType):
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
        spawn_thread=True,
    )
    def new_measured_field(
        self,
        field_type,
        source_type,
        scan_type,
        field_name,
        file_info_list,
        aut_size,
    ):

        # Read measured field file
        field_data = registry.loaders.fields.load(
            source=source_type,
            field_type=field_type,
            scan_type=scan_type,
            file_list=file_info_list,
        )
        field_data.attrs["aperture_size"] = aut_size
        print(field_data)

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
    _coordinates_node: CoordinateNode | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _field_type: FieldType = field(default=FieldType.UNKNOWN, init=False)
    _source_type: DataSource = field(
        default=DataSource(id="xnft.unknown", display_name="Unknown"),
        init=False,
    )

    name_editable: bool | None = True

    # TODO/FIXME: populate with exporter registry
    file_export_types: ClassVar[tuple[str, ...]] = (".h5", ".csv")

    def __init__(
        self,
        *,
        name: str | None = None,
        source: Node | None = None,
        coordinates_node: CoordinateNode | None = None,
        field_type: FieldType = FieldType.UNKNOWN,
        source_type: DataSource | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            node_type=NodeType.FIELDS,
            source=source,
            **kwargs,
        )

        if source_type is None:
            registry.data_sources.get("xnft.unknown")

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
    @gui_property(label="AUT Aperture Size", order=6)
    def aut_size_gui(self):
        return f"{Quantity(self.data.attrs['aperture_size'], units='m')}"

    @property
    @gui_property(label="Gain Calibration", order=7)
    def gain_calibration_gui(self):
        if self.data.attrs["gain_calibration"]:
            return f"{self.data.attrs['gain_calibration'].name}"
        return "None"

    @context_action(
        label="Export Field",
        enabled=True,
        tooltip="Write field data to file",
        icon_name="document-save",
        order=100,
        separator=True,
        action="ui_action",
        helper_dialog=ExportDataDialog,
        spawn_thread=True,
    )
    def export_data(self, file_path: Path):
        if self.data is None:
            return

        file_type = file_path.suffix

        if file_type == ".h5":
            write_dataset_hdf5(self.data, file_path)

        elif file_type == ".csv":
            self.data.to_dataframe().to_csv(file_path)
        else:
            raise NotImplementedError(
                f"File extention type of {file_type} is not implemented. "
                f"Available options are {', '.join(self.file_export_types)}",
            )
