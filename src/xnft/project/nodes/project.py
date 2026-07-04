"""
Handle xnft project actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import logging

from .node import Node, NodeType, context_action, gui_property
from .fields import FieldsNode
from .analysis import AnalysisNode
from .reports import ReportsNode
from .coordinates import CoordinatesNode
from .model import ModelNode
from .calibrations import PowerCalibrationsNode
from .probes import ProbesNode
from ..project_io import write_project

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Project(Node):
    """Project Node subclass to handle projects."""

    _path: Optional[Path] = None
    version: int = 1
    icon_name: str = "folder"
    # name: str | None = None

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        # Add default project nodes
        self.add_child(FieldsNode())
        self.add_child(ProbesNode())
        self.add_child(PowerCalibrationsNode())
        self.add_child(AnalysisNode())
        self.add_child(ReportsNode())
        self.add_child(CoordinatesNode())
        # self.add_child(ModelNode())  # Not yet implemented

        # Allow projects to be renamed in the Project Manager
        self.name_editable = True
        self.node_type = NodeType.PROJECT

    @property
    @gui_property(label="File Path", order=3)
    def path(self):
        return self._path
    
    @path.setter
    def path(self, new_path):
        self._path = Path(new_path)

    @context_action(
        "Save Project", order=10, enabled=True, icon_name="document-save"
    )
    def save(self, path=None):
        """Saves project to `self.path` specified at project creation.

        Parameters
        ----------
        path : Path, optional
            Path to save project to, by default None

        Returns
        -------
        str
            Status message to display in status bar in main window.
        """
        if path is not None:
            self._path = path

        try:
            write_project(self, compression_level=10)
            return f"Saved project {self.name} to path: {self._path}"
        except Exception:
            return f"Failed to save {self.name} to path: {self._path}"

    @context_action(
        "Save Project As...",
        order=10,
        enabled=False,
        icon_name="document-save",
    )
    def save_as(self, path=None):
        pass

    @context_action(
        "Close Project",
        order=20,
        enabled=False,
        icon_name="window-close",
        action="close_project",
        separator=True,
    )
    def close(self, path=None):
        pass
