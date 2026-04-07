"""
Handle xnft results node actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass, field, InitVar
from typing import Optional
import logging
from functools import partial

from PySide6.QtWidgets import QMdiSubWindow

from .node import Node, DataNode, NodeType, context_action, gui_property

from ...gui.dialogs.reports.new_field_report_dialog import (
    NewFieldReport,
)
from ...core.enums import ReportType
from ...core.reports.plot_2d import Plot2D
from ...core.reports.plot_1d import Plot1D

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ResultsNode(Node):
    icon_name: str = "src/xnft/resources/icons/plot.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.RESULTS
        self._name = NodeType.RESULTS

    @context_action(
        "New Line Plot",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=partial(NewFieldReport, show_fields=False),
        icon_name="document-new",
    )
    def new_1d_field_report(self, **kwargs):
        logger.debug(f'{kwargs=}')
        report_node = ReportNode(
            name=kwargs["report_name"],
            report_type=ReportType.PLOT_LINE,
            args=kwargs,
            source=None,
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new report"

        # Call ReportNode.open to open MDI windows on creation
        # append windows to result_dict

        result_dict = {"status": status, "nodes": node_pair_list}

        # Open the report
        result_dict.update(report_node.open())

        return result_dict

    @context_action(
        "New Surface Plot",
        order=20,
        enabled=True,
        action="ui_action",
        helper_dialog=partial(NewFieldReport, show_fields=True, select_multiple_fields=False),
        icon_name="document-new",
    )
    def new_2d_field_report(self, **kwargs):
        logger.debug(f'{kwargs=}')
        report_node = ReportNode(
            name=kwargs["report_name"],
            report_type=ReportType.PLOT_SURFACE_2D,
            fields=kwargs["fields"],
            args=kwargs,
            source=kwargs["fields"][0],
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new report"

        # Call ReportNode.open to open MDI windows on creation
        # append windows to result_dict

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

    report_type: InitVar[Optional[ReportType]] = None
    fields: InitVar[Optional[list]] = list()

    name_editable: Optional[bool] = True
    icon_name: str = "utilities-system-monitor"
    args: dict = field(default_factory=dict)

    def __post_init__(
            self, 
            name: Optional[str] = None, 
            node_type: Optional[NodeType] = NodeType.UNKNOWN,
            source: Optional[Node | None] = None,
            report_type: Optional[ReportType] = ReportType.UNKNOWN,
            fields: Optional[list] = list()
        ):
        super().__post_init__(name=name, node_type=node_type, source=source)
        
        self.node_type = NodeType.ANALYSIS
        self.report_type = report_type
        self.fields = fields

    @property
    @gui_property(label="Report Type", order=10)
    def report_type(self):
        return self._report_type
    
    @report_type.setter
    def report_type(self, report: ReportType):
        if not isinstance(report, ReportType):
            raise TypeError(f'Argument "report_type" must be of type {ReportType} got {type(report)}')
        self._report_type = report


    @context_action(
        label="View Report",
        icon_name="utilities-system-monitor",
        action="ui_action",
    )
    def open(self):
        """Open/view the report in an MDI window."""

        if self.report_type == ReportType.PLOT_LINE:
            plot_widget = Plot1D(self)
        elif self.report_type == ReportType.PLOT_SURFACE_2D:
            plot_widget = Plot2D(self)  # Should only be one field for 2D

        # TODO: Ideally the Qt code would live outside of this module
        win = QMdiSubWindow()
        win.setWidget(plot_widget)
        win.setWindowTitle(self.name)

        result_dict = {"windows": [win]}

        return result_dict
