"""
Handle xnft project actions.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

import logging
from typing import List

from .nodes.project import Project


logger = logging.getLogger(__name__)


# === Project Manager ===
class Manager:
    def __init__(self):
        self._projects: List[Project] = []

    @property
    def projects(self):
        return self._projects

    def add_project(self, project: Project):
        self._projects.append(project)

    def remove_project(self, project: Project):
        self._projects.remove(project)

    @property
    def project_count(self):
        return len(self._projects)

    def get_project_by_index(self, index):
        return self._projects[index]

    def index_of_project(self, project: Project):
        return self._projects.index(project)
