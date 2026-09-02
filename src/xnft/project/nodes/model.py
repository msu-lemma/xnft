"""
Handle xnft project actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from dataclasses import dataclass

from ...project.nodes.node import Node
from .node import NodeType, context_action

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ModelNode(Node):
    icon_name: str = "src/xnft/resources/icons/model.svg"

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

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
