"""
Handle xnft results node actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from PySide6.QtWidgets import QMdiSubWindow

from .node import Node, DataNode, NodeType, context_action

from ...gui.dialogs.reports.new_field_report_dialog import (
    NewFieldReport,
)
from ...core.types import ReportType
from ...core.plots import Plot2D

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ResultsNode(Node):
    icon_name: str = "src/xnft/resources/icons/plot.svg"
    type: NodeType = NodeType.RESULTS

    @context_action(
        "New Field Report",
        order=20,
        enabled=True,
        action="ui_action",
        helper_dialog=NewFieldReport,
        icon_name="document-new",
    )
    def new_field_report(self, **kwargs):
        report_node = ReportNode(
            name=kwargs["report_name"],
            type=kwargs["report_type"],
            field_type=kwargs["field_type"],
            fields=kwargs["fields"],
            frequencies=kwargs["frequencies"],
            args=kwargs,
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new report"

        # TODO: Call ReportNode.open to open MDI windows on creation
        #       append windows to result_dict

        result_dict = {"status": status, "nodes": node_pair_list}

        # Open the report
        result_dict.update(report_node.open())

        return result_dict

    @context_action(
        "New Antenna Parameters Report",
        order=30,
        enabled=False,
        icon_name="document-new",
    )
    def new_antenna_parameters_report(self):
        logger.warning("Antenna parametes report is not yet implemented.")


@dataclass(kw_only=True)
class ReportNode(DataNode):
    field_type: str | None = None
    fields: list = field(default_factory=list)
    frequencies: list = field(default_factory=list)
    name_editable: Optional[bool] = True
    icon_name: str = "utilities-system-monitor"
    args: dict = field(default_factory=dict)

    @context_action(
        label="View Report",
        icon_name="utilities-system-monitor",
        action="ui_action",
    )
    def open(self):
        """Open/view the report in an MDI window."""

        if self.type == ReportType.PLOT_2D:
            plot_widget = Plot2D(
                self.fields[0], projection="uv"
            )  # TODO FIXME should only be one field

        # TODO: Ideally the Qt code would live outside of this module
        win = QMdiSubWindow()
        win.setWidget(plot_widget)
        win.setWindowTitle(self.name)

        result_dict = {"windows": [win]}

        return result_dict
