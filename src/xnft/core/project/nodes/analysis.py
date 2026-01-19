"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from dataclasses import dataclass
import logging
from enum import StrEnum

from ....gui.dialogs.analysis.new_planar_nft_dialog import (
    NewPlanarNearFieldTransform,
)

from ...algorithms import (
    planar_near_field_transform,
    planar_near_field_transform_full,
)

from .node import Node, NodeType, menu_action

logger = logging.getLogger(__name__)





@dataclass(kw_only=True)
class AnalysisNode(Node):
    name: str = "Analysis"
    icon_name: str = "src/xnft/resources/icons/function.svg"
    type: NodeType = NodeType.ANALYSIS

    @menu_action(
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

        # Create the transform node item
        node = TransformNode(name=transform_name, data=data)

        # Prepare results
        pass

        node_pair_list = [(self, node)]
        status = "Near-to-far Field Transform is not yet implemented."

        return node_pair_list, status

    @menu_action(
        "New Spherical Near-to-far Field Transform", order=20, enabled=False
    )
    def new_spherical_nft(self):
        logger.warning("Near-to-far Field Transform is not yet implemented.")

    @menu_action(
        "New Near Field Interpolation", order=30, enabled=False, separator=True
    )
    def new_near_field_interpolation(self):
        logger.warning("Near field interpolation is not yet implemented.")

    @menu_action("New Far Field Interpolation", order=40, enabled=False)
    def new_far_field_interpolation(self):
        logger.warning("Far field interpolation is not yet implemented.")


@dataclass(kw_only=True)
class TransformNode(Node):
    pass
