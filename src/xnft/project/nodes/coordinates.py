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
    coordinate_type: InitVar[Optional[CoordinateSystemType]] = None

    # source: InitVar[Optional[Node]] = None

    name_editable: Optional[bool] = True

    def __post_init__(
            self, 
            name: Optional[str] = None, 
            node_type: Optional[NodeType] = NodeType.UNKNOWN,
            source: Optional[Node | None] = None,
            coordinate_type: Optional[CoordinateSystemType] = CoordinateSystemType.UNKNOWN,
        ):
        super().__post_init__(name=name, node_type=node_type, source=source)

        self.node_type = NodeType.COORDINATES
        self.coordinate_type = coordinate_type

    @property
    @gui_property(label="System", order=4)
    def coordinate_type(self):
        return self._coordinate_type
    
    @coordinate_type.setter
    def coordinate_type(self, system: CoordinateSystemType):
        if not isinstance(system, CoordinateSystemType):
            raise TypeError(f'Argument "system" must be of type {CoordinateSystemType} got {type(system)}')
        self._coordinate_type = system
