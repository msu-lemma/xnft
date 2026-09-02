"""
Handle create/modify analysis (field transforms).

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from dataclasses import dataclass, field

from ...core.algorithms.planar_near_field_transform import (
    planar_near_field_transform,
)
from ...core.antennas.probes.probes import MeasurementProbe, RectWaveguide
from ...core.enums import (
    AnalysisType,
    CoordinateSystemType,
    DataSourceType,
    FieldType,
    NodeType,
)
from ...gui.dialogs.analysis.new_planar_nft_dialog import (
    NewPlanarNearFieldTransform,
)
from .coordinates import CoordinateNode
from .fields import FieldNode
from .node import DataNode, Node, context_action, gui_property

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class AnalysisNode(Node):
    icon_name: str = "src/xnft/resources/icons/function.svg"

    def __post_init__(self, name: str | None = None, node_type: NodeType = NodeType.UNKNOWN):
        super().__post_init__(name, node_type)

        self._node_type = NodeType.ANALYSIS
        self._name = NodeType.ANALYSIS

    @context_action(
        "New Planar Near-to-far Field Transform",
        order=10,
        enabled=True,
        action="ui_action",
        helper_dialog=NewPlanarNearFieldTransform,
        icon_name="document-new",
        spawn_thread=True,
    )
    def new_planar_nft(
        self,
        transform_name,
        source_field,
        probe_correction,
        frequencies,
        gain_calibration,
    ):
        # Perform the near to far field transform
        field_data = planar_near_field_transform(
            near_field=source_field.data,
            probe_correction=probe_correction,
            frequencies=frequencies,
            gain_calibration=gain_calibration,
        )

        coordinate_data = field_data.coords
        coordinate_node = CoordinateNode(
            name=f"{transform_name} Coordinates",
            data=coordinate_data,
            coordinate_type=CoordinateSystemType.SPHERICAL,
            source=None,
        )

        # Create the transform node and field node
        field_node = FieldNode(
            name=transform_name,
            data=field_data,
            field_type=FieldType.FAR,
            coordinates_node=coordinate_node,
            source_type=DataSourceType.XNFT,
        )
        transform_node = TransformNode(
            name=transform_name,
            data=field_node,
            source=source_field,
            analysis_type=AnalysisType.PLANAR_TRANSFORM,
            probe_correction=probe_correction,
        )
        coordinate_node.source = field_node

        # Get the fields and coordinates root nodes to add far field node to
        fields_root_node = None
        coordinates_root_node = None
        for tmp_node in self.parent.children:
            if tmp_node.node_type == NodeType.FIELDS:
                fields_root_node = tmp_node
            if tmp_node.node_type == NodeType.COORDINATES:
                coordinates_root_node = tmp_node
        assert fields_root_node is not None
        assert coordinates_root_node is not None

        node_pair_list = [
            (self, transform_node),
            (fields_root_node, field_node),
            (coordinates_root_node, coordinate_node),
        ]

        # Status to display on status bar at bottom of window
        status = "Planar near-to-far field transform finished."

        result_dict = {"status": status, "nodes": node_pair_list}

        return result_dict

    @context_action(
        "New Spherical Near-to-far Field Transform",
        order=20,
        enabled=False,
        icon_name="document-new",
        spawn_thread=True,
    )
    def new_spherical_nft(self):
        logger.warning("Spherical near-to-far Field transform is not yet implemented.")

    @context_action(
        "New Near Field Interpolation",
        order=30,
        enabled=False,
        separator=True,
        icon_name="document-new",
        spawn_thread=True,
    )
    def new_near_field_interpolation(self):
        logger.warning("Near field interpolation is not yet implemented.")

    @context_action(
        "New Far Field Interpolation",
        order=40,
        enabled=False,
        icon_name="document-new",
        spawn_thread=True,
    )
    def new_far_field_interpolation(self):
        logger.warning("Far field interpolation is not yet implemented.")

    @context_action(
        "New Derived Field (Function)",
        order=50,
        enabled=False,
        separator=True,
        icon_name="document-new",
        spawn_thread=True,
    )
    def new_function(self):
        logger.warning("Derived are not yet implemented.")


@dataclass(kw_only=True)
class TransformNode(DataNode):
    _analysis_type: AnalysisType = field(
        default=AnalysisType.UNKNOWN,
        init=False,
        repr=False,
    )
    _probe_correction: MeasurementProbe = field(
        default=MeasurementProbe(
            "Unknown", RectWaveguide(float("nan"), float("nan"), (float("nan"), float("nan")))
        ),
        init=False,
        repr=False,
    )

    name_editable: bool | None = True

    def __init__(
        self,
        *,
        name: str | None = None,
        source: Node | None = None,
        analysis_type: AnalysisType = AnalysisType.UNKNOWN,
        probe_correction: MeasurementProbe = MeasurementProbe(
            "Unknown", RectWaveguide(float("nan"), float("nan"), (float("nan"), float("nan")))
        ),
        **kwargs,
    ):
        super().__init__(
            name=name,
            node_type=NodeType.ANALYSIS,
            source=source,
            # **kwargs,
        )

        self.analysis_type = analysis_type
        self._probe_correction = probe_correction

    @property
    @gui_property(label="Analysis Type", order=2)
    def analysis_type(self):
        return self._analysis_type

    @analysis_type.setter
    def analysis_type(self, analysis: AnalysisType):
        if not isinstance(analysis, AnalysisType):
            raise TypeError(
                f'Argument "analysis_type" must be of type {AnalysisType} got {type(self.analysis)}'
            )
        self._analysis_type = analysis

    @property
    @gui_property(label="Probe Correction", order=3)
    def probe_correction(self):
        if self._probe_correction:
            return f"{self._probe_correction.name} ({self._probe_correction.correction_type})"
        else:
            return "None"
