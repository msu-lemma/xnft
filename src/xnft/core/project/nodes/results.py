"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging
from .node import Node, NodeType, context_action

from ....gui.dialogs.reports.new_field_report_dialog import (
    NewFieldReport,
)

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ResultsNode(Node):
    name: str = "Results"
    icon_name: str = "src/xnft/resources/icons/plot.svg"
    type: NodeType = NodeType.RESULTS

    @context_action(
        "New Field Report",
        order=20,
        enabled=True,
        action="new_node",
        helper_dialog=NewFieldReport,
    )
    def new_field_report(
        self, report_name, report_type, field_type, fields, frequencies
    ):

        report_node = ReportNode(
            name=report_name,
            type=report_type,
            field_type=field_type,
            fields=fields,
            frequencies=frequencies
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Near-to-far Field Transform is not yet implemented."

        return node_pair_list, status

    @context_action("New Antenna Parameters Report", order=30, enabled=False)
    def new_antenna_parameters_report(self):
        logger.warning("Antenna parametes report is not yet implemented.")


@dataclass(kw_only=True)
class ReportNode(Node):
    field_type: str | None = None
    fields: list = field(default_factory=list)
    frequencies: list = field(default_factory=list)
    name_editable: Optional[bool] = True

    def edit(self):
        pass

    