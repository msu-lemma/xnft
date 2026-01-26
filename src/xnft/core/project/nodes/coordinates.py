"""
Handle xnft project actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass
from typing import Optional
import logging
from .node import Node, LeafNode, context_action
from ...types import NodeType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CoordinatesNode(Node):
    name: str = "Coordinates"
    icon_name: str = "src/xnft/resources/icons/coordinates.svg"
    type: NodeType = NodeType.COORDINATES

    @context_action(
        "New Measurement Coordinates",
        order=10,
        enabled=False,
        icon_name="document-new",
    )
    def new_measurement_coordinates(self):
        logger.warning("New measurement coordinates is not yet implemented.")


@dataclass(kw_only=True)
class CoordinateNode(LeafNode):
    source: Optional[Node]
    name_editable: Optional[bool] = True
