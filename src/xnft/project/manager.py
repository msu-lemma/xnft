"""
Project manager class.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State
University.
"""

import logging
from typing import List

from .nodes.project import Project

logger = logging.getLogger(__name__)


# === Project Manager ===
class Manager:
    def __init__(self, projects: List[Project] = []):
        self._projects = projects

    @property
    def projects(self):
        return self._projects

    @property
    def project_count(self):
        return len(self._projects)

    def add_project(self, project: Project):
        self._projects.append(project)

    def remove_project(self, project: Project):
        self._projects.remove(project)
        # TODO: handle removing project from memory

    def get_project_by_index(self, index):
        return self._projects[index]

    def index_of_project(self, project: Project):
        return next(idx for idx, proj in enumerate(self.projects) if proj is project)
