"""
Handle create/modify analysis (field transforms).

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass
from typing import Optional
import logging

from ...gui.dialogs.analysis.new_planar_nft_dialog import (
    NewPlanarNearFieldTransform,
)

from ...core.algorithms import (
    planar_near_field_transform,
)

from .node import Node, DataNode, context_action
from .fields import FieldNode
from .coordinates import CoordinateNode
from ...core.enums import NodeType, FieldType, DataSourceType, CoordinateSystemType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class AnalysisNode(Node):
    icon_name: str = "src/xnft/resources/icons/function.svg"
    type: NodeType = NodeType.ANALYSIS

    @context_action(
        "New Planar Near-to-far Field Transform",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=NewPlanarNearFieldTransform,
        icon_name="document-new",
    )
    def new_planar_nft(
        self,
        transform_name,
        source_field,
        probe_correction,
        frequencies,
    ):
        # Perform the near to far field transform
        field_data = planar_near_field_transform(
            near_field=source_field.data,
            probe_correction=probe_correction,
            frequencies=frequencies,
        )

        coordinate_data = field_data.coords
        coordinate_node = CoordinateNode(
            name=f"{transform_name} Coordinates",
            data=coordinate_data,
            type=CoordinateSystemType.SPHERICAL,
        )

        # Create the transform node and field node
        field_node = FieldNode(
            name=transform_name,
            data=field_data,
            type=FieldType.FAR,
            measured=False,
            coordinates=coordinate_node,
            source_type=DataSourceType.XNFT,
        )
        transform_node = TransformNode(name=transform_name, data=field_node)
        coordinate_node.source = field_node

        # Get the fields and coordinates root nodes to add far field node to
        fields_root_node = None
        coordinates_root_node = None
        for tmp_node in self.parent.children:
            if tmp_node.type == NodeType.FIELDS:
                fields_root_node = tmp_node
            if tmp_node.type == NodeType.COORDINATES:
                coordinates_root_node = tmp_node
        assert fields_root_node is not None
        assert coordinates_root_node is not None

        node_pair_list = [
            (self, transform_node),
            (fields_root_node, field_node),
            (coordinates_root_node, coordinate_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Near-to-far Field Transform is not yet implemented."

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict

    @context_action(
        "New Spherical Near-to-far Field Transform",
        order=20,
        enabled=False,
        icon_name="document-new",
    )
    def new_spherical_nft(self):
        logger.warning("Near-to-far Field Transform is not yet implemented.")

    @context_action(
        "New Near Field Interpolation",
        order=30,
        enabled=False,
        separator=True,
        icon_name="document-new",
    )
    def new_near_field_interpolation(self):
        logger.warning("Near field interpolation is not yet implemented.")

    @context_action(
        "New Far Field Interpolation",
        order=40,
        enabled=False,
        icon_name="document-new",
    )
    def new_far_field_interpolation(self):
        logger.warning("Far field interpolation is not yet implemented.")

    @context_action(
        "New Derived Field (Function)",
        order=50,
        enabled=False,
        separator=True,
        icon_name="document-new",
    )
    def new_function(self):
        logger.warning("Derived are not yet implemented.")


@dataclass(kw_only=True)
class TransformNode(DataNode):
    name_editable: Optional[bool] = True
