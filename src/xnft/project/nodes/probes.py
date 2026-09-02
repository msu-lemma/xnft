"""
Handle xnft probes node actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from dataclasses import dataclass, field

from quantiphy import Quantity

from ...core.antennas.probes.probes import MeasurementProbe
from ...core.enums import ProbeType
from ...gui.dialogs.probes.new_probe_dialog import NewProbeDialog
from .node import DataNode, Node, NodeType, context_action, gui_property

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ProbesNode(Node):
    icon_name: str = "src/xnft/resources/icons/probe.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.PROBES
        self._name = NodeType.PROBES

    @context_action(
        "New Measurement Probe",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=NewProbeDialog,
        icon_name="document-new",
    )
    def new_probe(self, **kwargs):
        logger.debug(f"{kwargs=}")
        report_node = ProbeNode(
            probe=kwargs["probe"],
        )

        node_pair_list = [
            (self, report_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Created new measurement probe"

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict


@dataclass(kw_only=True, eq=False)
class ProbeNode(DataNode):
    _probe: MeasurementProbe = field(init=False, repr=False)

    name_editable: bool | None = True
    # icon_name: str = "utilities-system-monitor"

    def __init__(
        self,
        *,
        probe: MeasurementProbe,
        **kwargs,
    ):
        kwargs.pop("args", None)

        super().__init__(
            name=probe.name,
            node_type=NodeType.PROBES,
            **kwargs,
        )

        self.probe = probe

    @property
    @gui_property(label="Probe Correction Type", order=10)
    def correction_type(self):
        return self.probe.correction_type

    @property
    @gui_property(label="Dimensions", order=20)
    def dimensions(self):
        if self.correction_type == ProbeType.IDEAL_RECT:
            xdim = f"{Quantity(self.probe.source.x, units='m')}"
            ydim = f"{Quantity(self.probe.source.y, units='m')}"
            result_str = f"{xdim} ✕ {ydim}"
        else:
            result_str = ""
        return result_str

    @property
    @gui_property(label="Frequency Band", order=30)
    def frequency_band(self):
        if self.correction_type == ProbeType.IDEAL_RECT:
            band_low = f"{Quantity(self.probe.source.band[0], units='Hz')}"
            band_high = f"{Quantity(self.probe.source.band[1], units='Hz')}"
            result_str = f"{band_low}–{band_high}"
        else:
            result_str = ""
        return result_str
