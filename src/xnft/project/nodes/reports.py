"""
Handle xnft results node actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

import numpy as np
import xarray as xr
from PySide6.QtWidgets import QMdiSubWindow

from ...core.data_writers import write_data_array_hdf5
from ...core.enums import ReportType
from ...core.reports.plot_1d import Plot1D, PlotTrace
from ...core.reports.plot_2d import (
    Plot2D,
    SurfacePlot2DParameters,
    get_transformed_data,
)
from ...gui.dialogs.export_data_dialog import ExportDataDialog
from ...gui.dialogs.export_data_directory_dialog import ExportDataDirectoryDialog
from ...gui.dialogs.reports.new_field_report_dialog import NewFieldReport
from .node import DataNode, Node, NodeType, context_action, gui_property

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ReportsNode(Node):
    icon_name: str = "src/xnft/resources/icons/plot.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.REPORTS
        self._name = NodeType.REPORTS

    @context_action(
        "New Line Plot",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=partial(NewFieldReport, show_fields=False),
        icon_name="document-new",
    )
    def new_1d_field_report(self, **kwargs):
        report_node = ReportNodeLinePlot(
            name=kwargs["report_name"],
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
        report_node = ReportNodeSurfacePlot2D(
            name=kwargs["report_name"],
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


@dataclass(kw_only=True, eq=False)
class ReportNode(DataNode):
    _report_type: ReportType = field(init=False, repr=False)
    fields: list = field(default_factory=list)
    args: dict = field(default_factory=dict)

    name_editable: bool | None = True
    icon_name: str = "utilities-system-monitor"

    file_export_types = [".h5", ".csv"]

    def __init__(
        self,
        *,
        name: str | None = None,
        source: Node | None = None,
        fields: list | None = None,
        args: dict | None = None,
        report_type: ReportType = ReportType.UNKNOWN,
        **kwargs,
    ):
        kwargs.pop("args", None)

        super().__init__(
            name=name,
            node_type=NodeType.REPORTS,
            source=source,
            **kwargs,
        )

        self.fields = fields or []
        self.args = args or {}
        self.report_type = report_type

    @property
    @gui_property(label="Report Type", order=10)
    def report_type(self):
        return self._report_type

    @report_type.setter
    def report_type(self, report: ReportType):
        if not isinstance(report, ReportType):
            raise TypeError(
                f'Argument "report_type" must be of type {ReportType} got {type(report)}'
            )
        self._report_type = report


@dataclass(kw_only=True)
class ReportNodeSurfacePlot2D(ReportNode):
    icon_name: str = "utilities-system-monitor"

    def __init__(
        self,
        *,
        name: str | None = None,
        source: Node | None = None,
        fields: list | None = None,
        args: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            source=source,
            fields=fields,
            args=args,
            report_type=ReportType.PLOT_SURFACE_2D,
            **kwargs,
        )

        self.file_export_types = [".h5", ".csv"]

    @context_action(
        label="View Report", icon_name="utilities-system-monitor", action="ui_action", order=10
    )
    def open(self):
        """Open/view the report in an MDI window."""
        plot_widget = Plot2D(self)  # Should only be one field for 2D

        # TODO: Ideally the Qt code would live outside of this module
        win = QMdiSubWindow()
        win.setWidget(plot_widget)
        win.setWindowTitle(self.name)

        result_dict = {"windows": [win]}

        return result_dict

    @context_action(
        label="Export Report Values",
        enabled=True,
        tooltip="Write report data to file",
        icon_name="document-save",
        order=100,
        # separator=True,
        action="ui_action",
        helper_dialog=ExportDataDialog,
    )
    def export_data(self, file_path: Path):
        file_type = file_path.suffix

        if not isinstance(self.data, SurfacePlot2DParameters):
            raise TypeError(
                f"Export data must be of type SurfacePlot2DParameters not {type(self.data)}"
            )

        field_values, axes_dict = get_transformed_data(self.data)
        report_data = xr.DataArray(
            data=np.squeeze(field_values),
            name="field_value",
            attrs=self.data.serialize(),
            coords={
                "x": (
                    "x",
                    axes_dict["x"].values,
                    {
                        "long_name": axes_dict["x"].label,
                        "units": str(axes_dict["x"].units),
                    },
                ),
                "y": (
                    "y",
                    axes_dict["y"].values,
                    {
                        "long_name": axes_dict["y"].label,
                        "units": str(axes_dict["y"].units),
                    },
                ),
            },
        )

        if file_type == ".h5":
            write_data_array_hdf5(report_data, file_path=file_path)
        elif file_type == ".csv":
            report_data.to_dataframe().to_csv(file_path)
        else:
            raise NotImplementedError(
                f"File extention type of {file_type} is not implemented. "
                f"Available options are {', '.join(self.file_export_types)}"
            )


@dataclass(kw_only=True)
class ReportNodeLinePlot(ReportNode):
    # icon_name: str = "utilities-system-monitor"

    # args: dict = field(default_factory=dict)

    # def __init__(
    #     self,
    #     *,
    #     name: Optional[str] = None,
    #     source: Optional[Node] = None,
    #     args: Optional[dict] = None,
    #     **kwargs,
    # ):
    #     kwargs.pop("args", None)

    #     super().__init__(name=name, node_type=NodeType.REPORTS, source=source, **kwargs)

    #     self.args = args or {}
    #     self.report_type = ReportType.PLOT_LINE
    #     self.file_export_types = [".h5", ".csv"]
    icon_name: str = "utilities-system-monitor"

    def __init__(
        self,
        *,
        name: str | None = None,
        source: Node | None = None,
        args: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            source=source,
            args=args,
            report_type=ReportType.PLOT_LINE,
            **kwargs,
        )

        self.file_export_types = [".h5", ".csv"]

    @context_action(
        label="View Report", icon_name="utilities-system-monitor", action="ui_action", order=10
    )
    def open(self):
        """Open/view the report in an MDI window."""
        plot_widget = Plot1D(self)

        # TODO: Ideally the Qt code would live outside of this module
        win = QMdiSubWindow()
        win.setWidget(plot_widget)
        win.setWindowTitle(self.name)

        result_dict = {"windows": [win]}

        return result_dict

    @context_action(
        label="Export Report Values",
        enabled=True,
        tooltip="Write report data to files",
        icon_name="document-save",
        order=100,
        # separator=True,
        action="ui_action",
        helper_dialog=partial(
            ExportDataDirectoryDialog,
            help_str="A single file will be created for each trace in the output directory.",
        ),
    )
    def export_data(self, directory_path: Path, file_type: str):
        # Iterate over each trace to write to output directory
        if not isinstance(self.data, Iterable):
            raise TypeError("self.data (traces) must be iterable")
        for trace in self.data:
            if not isinstance(trace, PlotTrace):
                raise TypeError(f"Export traces must be of type PlotTrace not {type(trace)}")

            plot_data, attrs = trace.serialize()
            report_data = xr.DataArray(
                data=plot_data["y"],
                name="field_value",
                attrs=attrs,
                coords={
                    "x": ("x", plot_data["x"]),
                },
            )

            file_path = Path(directory_path) / f'{attrs['name']}{file_type[1:]}'

            if file_type == "*.h5":
                write_data_array_hdf5(report_data, file_path)
            elif file_type == "*.csv":
                report_data.to_dataframe().to_csv(file_path)
            else:
                raise NotImplementedError(
                    f"File extention type of {file_type} is not implemented. "
                    f"Available options are {', '.join(self.file_export_types)}"
                )
