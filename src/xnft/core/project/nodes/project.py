"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import logging

from .node import Node, NodeType, menu_action
from .fields import FieldsNode
from .analyses import AnalysesNode
from .results import ResultsNode
from .coordinates import CoordinatesNode
from .model import ModelNode

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Project(Node):
    path: Optional[Path] = None
    version: int = 1
    type: NodeType = NodeType.PROJECT
    icon_name: str = "folder"

    def __post_init__(self):
        # Add default project nodes
        self.add_child(FieldsNode())
        self.add_child(AnalysesNode())
        self.add_child(ResultsNode())
        self.add_child(CoordinatesNode())
        self.add_child(ModelNode())

        # Allow projects to be renamed in the Project Manager
        self.name_editable = True

    @menu_action(
        "Save Project", order=10, enabled=True, icon_name="document-save"
    )
    def save(self, path=None):
        if path is not None:
            self.path = path
        logger.warning("Project saving not yet implemented.")
        return f"Failed to save {self.name} to path: {self.path}"
