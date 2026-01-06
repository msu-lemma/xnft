"""
Handle xnft project actions.
"""

from dataclasses import dataclass
import logging
from .node import Node, NodeType, menu_action

logger = logging.getLogger(__name__)



@dataclass(kw_only=True)
class ResultsNode(Node):
    name: str = "Results"
    icon_name: str = "src/xnft/resources/icons/plot.svg"
    type: NodeType = NodeType.RESTULTS

    @menu_action("New Near Field Report", order=10, enabled=False)
    def new_near_field_report(self):
        logger.warning("Near field report is not yet implemented.")

    @menu_action("New Far Field Report", order=20, enabled=False)
    def new_far_field_report(self):
        logger.warning("Near field report is not yet implemented.")

    @menu_action("New Antenna Parameters Report", order=30, enabled=False)
    def new_antenna_parameters_report(self):
        logger.warning("Antenna parametes report is not yet implemented.")

