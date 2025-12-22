"""
Handle xnft project actions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from uuid import uuid4
from pathlib import Path

@dataclass
class Node:
    # Node values
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = field(default="None")
    attributes: Optional[dict] = field(default_factory=dict)
    data: Optional[object] = None

    # Node traversal pointers
    _parent: Optional["Node"] = None
    _children: List["Node"] = field(default_factory=list)

    # -- Parents --

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if isinstance(parent, (Node, Project)):
            self._parent = parent
        else:
            raise TypeError(
                f"Node 'parent' must be of type 'Node' or 'Project',"
                f" got {type(parent)}."
            )

    # -- Children --

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        # Check type of children
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        if isinstance(child, Node):
            child.parent = self
            self._children.append(child)
        else:
            raise TypeError(
                f"Node children must be of type 'Node',"
                f" got {type(child)}."
            )
        
    @property
    def child_count(self):
        return len(self._children)

    # -- Node properties --

    @property
    def is_leaf(self):
        return len(self._children) == 0

    @property
    def is_root(self):
        return False if self.parent else True
    
    def get_child_by_index(self, index):
        return self._children[index]
    
    def index_of_node(self, node: "Node"):
        return self._children.index(node)


@dataclass(kw_only=True)
class Project(Node):
    path: Optional[Path] = None
    version: int = 1

    def save(self, path):
        if path is not None:
            self.path = path

        pass # TODO


class Manager():
    def __init__(self):
        self._projects: List[Project] = []

    @property
    def projects(self):
        return self._projects
    
    def add_project(self, project: Project):
        self._projects.append(project)

    @property
    def project_count(self):
        return len(self._projects)
    
    def get_project_by_index(self, index):
        return self._projects[index]

    def index_of_project(self, project: Project):
        return self._projects.index(project)
