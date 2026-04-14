"""
Handle xnft coordinates actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from dataclasses import dataclass, field, InitVar
from typing import Optional
import logging
from .node import Node, DataNode, context_action, gui_property
from ...core.enums import NodeType, CoordinateSystemType

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CoordinatesNode(Node):
    icon_name: str = "src/xnft/resources/icons/coordinates.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self._node_type = NodeType.COORDINATES
        self._name = NodeType.COORDINATES

    @context_action(
        "New Measurement Coordinates",
        order=10,
        enabled=False,
        icon_name="document-new",
    )
    def new_measurement_coordinates(self):
        logger.warning("New measurement coordinates is not yet implemented.")


@dataclass(kw_only=True)
class CoordinateNode(DataNode):
    _coordinate_type: CoordinateSystemType = field(
        default=CoordinateSystemType.UNKNOWN,
        init=False,
        repr=False,
    )

    name_editable: Optional[bool] = True

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        source: Optional[Node] = None,
        coordinate_type: CoordinateSystemType = CoordinateSystemType.UNKNOWN,
        **kwargs,
    ):
        super().__init__(
            name=name,
            node_type=NodeType.COORDINATES,
            source=source,
            **kwargs,
        )
        self.coordinate_type = coordinate_type

    @property
    @gui_property(label="System", order=4)
    def coordinate_type(self):
        return self._coordinate_type

    @coordinate_type.setter
    def coordinate_type(self, system: CoordinateSystemType):
        if not isinstance(system, CoordinateSystemType):
            raise TypeError(
                f'Argument "system" must be of type {CoordinateSystemType} got {type(system)}'
            )
        self._coordinate_type = system
