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
from ...gui.dialogs.calibrations.new_gain_calibration_dialog import NewGainCalibrationDialog
from ...core.calibration.gain import GainCalibrationReference
from .fields import FieldNode

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class GainCalibrationsNode(Node):
    icon_name: str = "src/xnft/resources/icons/calibration2.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.CALS
        self._name = NodeType.CALS

    @context_action(
        "New Gain Calibration",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=NewGainCalibrationDialog,
        icon_name="document-new",
    )
    def new_calibration(self, **kwargs):
        logger.debug(f"{kwargs=}")
        report_node = GainCalibrationNode(
            gain_cal_name=kwargs["gain_cal_name"],
            gain_cal_ref=kwargs["gain_cal_ref"],
            gain_cal_field=kwargs["gain_cal_field"]
        )
        logger.debug(f"{report_node=}")

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new gain calibration"

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict


@dataclass(kw_only=True, eq=False)
class GainCalibrationNode(DataNode):
    # _gain_cal_name: str
    # _gain_cal_ref: GainCalibration
    # _gain_cal_field: FieldNode

    name_editable: Optional[bool] = True
    # icon_name: str = "utilities-system-monitor"

    def __init__(
        self,
        *,
        gain_cal_name: str,
        gain_cal_ref: GainCalibrationReference,
        gain_cal_field: FieldNode,
        **kwargs,
    ):
        kwargs.pop("args", None)

        super().__init__(
            name=gain_cal_name,
            node_type=NodeType.CALS,
            **kwargs,
        )

        self.gain_cal_ref = gain_cal_ref
        self.gain_cal_field = gain_cal_field

    @property
    @gui_property(label="Reference Mfr.", order=30)
    def ref_manufacturer(self):
        return self.gain_cal_ref.manufacturer
    
    @property
    @gui_property(label="Reference Model", order=40)
    def ref_model(self):
        return self.gain_cal_ref.model
    
    @property
    @gui_property(label="Reference Serial Number", order=50)
    def ref_serial(self):
        return self.gain_cal_ref.serial

    @property
    @gui_property(label="Reference Field", order=60)
    def ref_field_name(self):
        return self.gain_cal_field._name
