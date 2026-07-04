"""
Handle xnft calibrations node actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging
from functools import partial
from quantiphy import Quantity

from ...core.apertures.probes import MeasurementProbe
from .node import Node, DataNode, NodeType, context_action, gui_property
from ...gui.dialogs.calibrations.new_power_calibration_dialog import NewPowerCalibrationDialog

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PowerCalibrationsNode(Node):
    icon_name: str = "src/xnft/resources/icons/calibration2.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.CALS
        self._name = NodeType.CALS

    @context_action(
        "New Power Calibration",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=NewPowerCalibrationDialog,
        icon_name="document-new",
    )
    def new_calibration(self, **kwargs):
        logger.debug(f"{kwargs=}")
        report_node = PowerCalibrationNode(
            probe=kwargs["probe"],
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new power calibration"

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict


@dataclass(kw_only=True, eq=False)
class PowerCalibrationNode(DataNode):
    # _probe: MeasurementProbe = field(init=False, repr=False)

    name_editable: Optional[bool] = True
    # icon_name: str = "utilities-system-monitor"

    def __init__(
        self,
        *,
        probe: MeasurementProbe,
        **kwargs,
    ):
        kwargs.pop("args", None)

        super().__init__(
            # name=probe.name,
            node_type=NodeType.PROBES,
            **kwargs,
        )

    @property
    @gui_property(label="Frequency Band", order=30)
    def frequency_band(self):
        result_str = ""
        return result_str

    @property
    @gui_property(label="Frequency Samples", order=40)
    def frequency_samples(self):
        result_str = ""
        return result_str
