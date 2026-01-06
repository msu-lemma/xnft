"""
Handle xnft project actions.
"""

from dataclasses import dataclass
import logging

from .node import Node, NodeType, menu_action

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ModelNode(Node):
    name: str = "Model"
    icon_name: str = "src/xnft/resources/icons/model.svg"
    type: NodeType = NodeType.MODEL

    @menu_action("New Model Asset", order=10, enabled=False)
    def new_measurement_coordinates(self):
        logger.warning("New model asset is not yet implemented.")

