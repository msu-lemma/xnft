"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from dataclasses import dataclass
from typing import Optional
import logging

from ....gui.dialogs.analysis.new_planar_nft_dialog import (
    NewPlanarNearFieldTransform,
)

from ...algorithms import (
    planar_near_field_transform,
    planar_near_field_transform_full,
)

from .node import Node, context_action
from .fields import FieldNode
from ...types import NodeType, FieldType, DataSourceType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class AnalysisNode(Node):
    name: str = "Analysis"
    icon_name: str = "src/xnft/resources/icons/function.svg"
    type: NodeType = NodeType.ANALYSIS

    @context_action(
        "New Planar Near-to-far Field Transform",
        order=10,
        enabled=True,
        action="new_node",
        helper_dialog=NewPlanarNearFieldTransform,
    )
    def new_planar_nft(
        self,
        transform_name,
        source_field,
        far_field,
        probe_correction,
        fft_x_size,
        fft_y_size,
        frequencies,
    ):
        # Perform the near to far field transform
        data = planar_near_field_transform(
            near_field_data=source_field.data,
            far_field_data=far_field.data,
            xfft_size=fft_x_size,
            yfft_size=fft_y_size,
            probe_correction=probe_correction,
            frequencies=frequencies,
        )

        # Create the transform node and field node
        far_field_node = FieldNode(
            name=transform_name,
            data=data,
            type=FieldType.FAR,
            source_type=DataSourceType.XNFT,
        )
        transform_node = TransformNode(
            name=transform_name, data=far_field_node
        )

        # Get the fields root node to add far field node to
        fields_node = None
        for tmp_node in self.parent.children:
            if tmp_node.name == "Fields":
                fields_node = tmp_node
                break
        assert fields_node is not None

        node_pair_list = [
            (self, transform_node),
            (fields_node, far_field_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Near-to-far Field Transform is not yet implemented."

        return node_pair_list, status

    @context_action(
        "New Spherical Near-to-far Field Transform", order=20, enabled=False
    )
    def new_spherical_nft(self):
        logger.warning("Near-to-far Field Transform is not yet implemented.")

    @context_action(
        "New Near Field Interpolation", order=30, enabled=False, separator=True
    )
    def new_near_field_interpolation(self):
        logger.warning("Near field interpolation is not yet implemented.")

    @context_action("New Far Field Interpolation", order=40, enabled=False)
    def new_far_field_interpolation(self):
        logger.warning("Far field interpolation is not yet implemented.")


@dataclass(kw_only=True)
class TransformNode(Node):
    name_editable: Optional[bool] = True
