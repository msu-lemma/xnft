"""
Handle xnft project actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass, InitVar
import logging
from typing import Optional
from ...project.nodes.node import Node

from .node import DataNode, NodeType, context_action

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ModelNode(DataNode):
    source: InitVar[Optional[Node]] = None
    icon_name: str = "src/xnft/resources/icons/model.svg"
    
    def __post_init__(
            self, 
            name: Optional[str] = None, 
            node_type: Optional[NodeType] = NodeType.UNKNOWN,
            source: Optional[Node | None] = None,
    ):
        super().__post_init__(name=name, node_type=node_type, source=source)

        self._node_type = NodeType.MODEL
        self._name = NodeType.MODEL

    @context_action(
        "New Model Asset",
        order=10,
        enabled=False,
        icon_name="document-new",
    )
    def new_measurement_coordinates(self):
        logger.warning("New model asset is not yet implemented.")
