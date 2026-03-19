"""
Abstract base class for nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Iterator
from typing import Self


class TreeNode(metaclass=ABCMeta):
    """
    Abstract base class for nodes in a tree structure.

    Different types of nodes are supported, analogous to Document Object Model (DOM)
    nodes, such as document, element, text, comment nodes, etc.

    TreeNodes are initially "floating" without parent or children.
    They are added to a tree via `append_child`, which sets up parent/child
    relationships. Adding an existing node elsewhere will raise an error.
    """

    parent_node: None | TreeNode
    children: list[TreeNode]

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

    def __iter__(self) -> Iterator[TreeNode]:
        """Iterate over direct children of this node."""
        return iter(self.children)

    def walk(self) -> Iterator[TreeNode]:
        """Depth-first traversal of this node and all descendants."""
        yield self
        for child in self.children:
            yield from child.walk()

    def append_child(self, child: TreeNode) -> None:
        """Add a child node to this node."""
        if child is self:
            raise ValueError("Can't make a node a child of itself")

        if not isinstance(child, TreeNode):
            raise ValueError(f"TreeNode can only contain other nodes. Unexpected type {child.__class__.__name__!r}")

        if child.parent_node is not None:
            raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent_node!r}")

        child.parent_node = self
        self.children.append(child)

    def remove_child(self, child: TreeNode) -> None:
        """Remove a child node from this node."""
        if child not in self.children:
            raise ValueError(f"TreeNode {child!r} is not a child of this node {self!r}")

        self.children.remove(child)
        child.parent_node = None

    def insert_before(self, new_child: TreeNode, reference: TreeNode) -> None:
        """Insert new_child before reference in this node's children."""
        if new_child is self:
            raise ValueError("Can't make a node a child of itself")
        if not isinstance(new_child, TreeNode):
            raise ValueError(f"TreeNode can only contain other nodes. Unexpected type {new_child.__class__.__name__!r}")
        if reference not in self.children:
            raise ValueError(f"Reference node {reference!r} is not a child of this node")
        if new_child.parent_node is not None:
            raise ValueError(f"Child {new_child!r} is already in the tree. Parent: {new_child.parent_node!r}")

        idx = self.children.index(reference)
        new_child.parent_node = self
        self.children.insert(idx, new_child)

    def replace_child(self, new_child: TreeNode, old_child: TreeNode) -> TreeNode:
        """Replace old_child with new_child. Returns old_child."""
        if new_child is self:
            raise ValueError("Can't make a node a child of itself")
        if not isinstance(new_child, TreeNode):
            raise ValueError(f"TreeNode can only contain other nodes. Unexpected type {new_child.__class__.__name__!r}")
        if old_child not in self.children:
            raise ValueError(f"TreeNode {old_child!r} is not a child of this node")
        if new_child.parent_node is not None:
            raise ValueError(f"Child {new_child!r} is already in the tree. Parent: {new_child.parent_node!r}")

        idx = self.children.index(old_child)
        old_child.parent_node = None
        new_child.parent_node = self
        self.children[idx] = new_child
        return old_child

    def remove(self) -> None:
        """Remove this node from its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot remove a node that has no parent")
        self.parent_node.remove_child(self)

    def replace_with(self, *nodes: TreeNode) -> None:
        """Replace this node in its parent with one or more nodes."""
        if self.parent_node is None:
            raise ValueError("Cannot replace a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self)
        self.parent_node = None
        parent.children.pop(idx)

        for offset, node in enumerate(nodes):
            if node.parent_node is not None:
                raise ValueError(f"Child {node!r} is already in the tree. Parent: {node.parent_node!r}")
            node.parent_node = parent
            parent.children.insert(idx + offset, node)

    def before(self, *nodes: TreeNode) -> None:
        """Insert nodes before this node in its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot insert before a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self)

        for offset, node in enumerate(nodes):
            if node.parent_node is not None:
                raise ValueError(f"Child {node!r} is already in the tree. Parent: {node.parent_node!r}")
            node.parent_node = parent
            parent.children.insert(idx + offset, node)

    def after(self, *nodes: TreeNode) -> None:
        """Insert nodes after this node in its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot insert after a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self) + 1

        for offset, node in enumerate(nodes):
            if node.parent_node is not None:
                raise ValueError(f"Child {node!r} is already in the tree. Parent: {node.parent_node!r}")
            node.parent_node = parent
            parent.children.insert(idx + offset, node)

    def prepend(self, *nodes: TreeNode) -> None:
        """Insert nodes at the beginning of this node's children."""
        for offset, node in enumerate(nodes):
            if node is self:
                raise ValueError("Can't make a node a child of itself")
            if not isinstance(node, TreeNode):
                raise ValueError(f"TreeNode can only contain other nodes. Unexpected type {node.__class__.__name__!r}")
            if node.parent_node is not None:
                raise ValueError(f"Child {node!r} is already in the tree. Parent: {node.parent_node!r}")
            node.parent_node = self
            self.children.insert(offset, node)

    def contains(self, node: TreeNode) -> bool:
        """Check if node is a descendant of this node."""
        return any(descendant is node for descendant in self.walk())

    @property
    def first_child(self) -> TreeNode | None:
        """The first child of this node, or None if it has no children."""
        if self.children:
            return self.children[0]
        return None

    @property
    def last_child(self) -> TreeNode | None:
        """The last child of this node, or None if it has no children."""
        if self.children:
            return self.children[-1]
        return None

    @property
    def next_sibling(self) -> TreeNode | None:
        """The next sibling of this node, or None if it has no next sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index + 1 < len(siblings):
            return siblings[index + 1]
        return None

    @property
    def previous_sibling(self) -> TreeNode | None:
        """The previous sibling of this node, or None if it has no previous sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index - 1 >= 0:
            return siblings[index - 1]
        return None

    def clone_node(self, deep: bool = False) -> Self:
        """Clone this node. If deep=True, clone all descendants too."""
        if deep:
            return copy.replace(self)
        return copy.replace(self, children=[])

    @abstractmethod
    def render(self, *args, **kwargs) -> Generator[str]:
        raise NotImplementedError("Subclasses must implement render")
