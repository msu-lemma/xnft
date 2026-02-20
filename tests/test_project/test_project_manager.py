"""Test theory file loader."""
import pytest

from xnft.core.types import FieldType, DataSourceType, FileInfo, PolarizationType
from xnft.project import manager
from xnft.project.nodes.project import Project


def test_init_project_manager():
    pm = manager.Manager()
    assert pm.projects == []


def test_add_project():
    pm = manager.Manager()
    project = Project()
    
    pm.add_project(project)

    assert pm.project_count == 1
    assert pm.projects[0] == project


def test_get_project_by_index():
    project_list = [Project() for _ in range(10)]
    pm = manager.Manager(project_list)

    for idx, project in enumerate(project_list):
        assert project == pm.get_project_by_index(idx)


def test_get_index_of_project():
    project_list = [Project() for _ in range(10)]
    pm = manager.Manager(project_list)

    for idx, project in enumerate(project_list):
        assert idx == pm.index_of_project(project)
