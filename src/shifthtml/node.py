"""
Abstract base class for nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Iterator


class Node(metaclass=ABCMeta):
    """
    Abstract base class for nodes in a tree structure.

    Different types of nodes are supported, analogous to Document Object Model (DOM)
    nodes, such as document, element, text, comment nodes, etc.

    Nodes are initially "floating" without parent or children.
    They are added to a tree via `append_child`, which sets up parent/child
    relationships. Adding an existing node elsewhere will raise an error.
    """

    parent_node: None | Node
    children: list[Node]

    def __init__(self):
        self.parent_node = None
        self.children = []

    def __replace__(self, /, **changes):
        new_obj = type(self)()
        new_children = changes.get("children", self.children)

        if new_children:
            for child in new_children:
                new_obj.append_child(copy.replace(child))

        return new_obj

    def __iter__(self) -> Iterator[Node]:
        """Iterate over direct children of this node."""
        return iter(self.children)

    def walk(self) -> Iterator[Node]:
        """Depth-first traversal of this node and all descendants."""
        yield self
        for child in self.children:
            yield from child.walk()

    def append_child(self, child: Node) -> None:
        """Add a child node to this node."""
        if child is self:
            raise ValueError("Can't make a node a child of itself")

        if not isinstance(child, Node):
            raise ValueError(f"Node can only contain other nodes. Unexpected type {child.__class__.__name__!r}")

        if child.parent_node is not None:
            raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent_node!r}")

        child.parent_node = self
        self.children.append(child)

    def remove_child(self, child: Node) -> None:
        """Remove a child node from this node."""
        if child not in self.children:
            raise ValueError(f"Node {child!r} is not a child of this node {self!r}")

        self.children.remove(child)
        child.parent_node = None

    @property
    def first_child(self) -> Node | None:
        """The first child of this node, or None if it has no children."""
        if self.children:
            return self.children[0]
        return None

    @property
    def last_child(self) -> Node | None:
        """The last child of this node, or None if it has no children."""
        if self.children:
            return self.children[-1]
        return None

    @property
    def next_sibling(self) -> Node | None:
        """The next sibling of this node, or None if it has no next sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index + 1 < len(siblings):
            return siblings[index + 1]
        return None

    @property
    def previous_sibling(self) -> Node | None:
        """The previous sibling of this node, or None if it has no previous sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index - 1 >= 0:
            return siblings[index - 1]
        return None

    @abstractmethod
    def render(self, *args, **kwargs) -> Generator[str]:
        raise NotImplementedError("Subclasses must implement render")
