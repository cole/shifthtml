from __future__ import annotations

import copy
from collections.abc import Generator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Node(Protocol):
    """
    A node in the document tree. Usually an HTML element or text content.

    Nodes have one parent and zero or more children. They are initialized without these,
    and then put into the tree via `add_child`.  `add_child` creates a copy of the
    node being added.

    Nodes exist inside of NodeTree objects.
    """

    parent: None | Node
    children: list[Node]

    def __init__(self, *args, **kwargs):
        self.parent = None
        self.children = []

    def __replace__(self, /, **changes):
        new_obj = type(self)()
        new_children = changes.get("children", self.children)

        if new_children:
            for child in new_children:
                new_obj.add_child(copy.replace(child))

        return new_obj

    def __iter__(self) -> Generator[Node]:
        """Iterate over all nodes in the tree."""
        yield self
        for child in self.children:
            yield from iter(child)

    def add_child(self, child: Node) -> None:
        """Add a child node to this node."""
        if child is self:
            raise ValueError("Can't make a node a child of itself")

        if isinstance(child, Node):
            if child.parent is not None:
                raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent!r}")
            child.parent = self
            self.children.append(child)
        else:
            raise ValueError(f"Node can only contain other nodes. Unexpected type {child.__class__.__name__!r}")

    def render(self, *args, **kwargs) -> Generator[str]:
        raise NotImplementedError("Node subclasses must implement render")


def _copy_tree(old_node: Node, pointer_target: Node) -> tuple[Node, Node | None]:
    pointer_found, child_pointer_found = None, None

    new_node = copy.replace(old_node, children=[])

    if old_node is pointer_target:
        pointer_found = new_node

    for child in old_node.children:
        new_child, child_pointer_found = _copy_tree(child, pointer_target)
        new_node.add_child(new_child)

    return new_node, pointer_found or child_pointer_found


@runtime_checkable
class NodeTree(Protocol):
    root: Node
    append_pointer: Node

    def __init__(self, root: Node, append_pointer: Node, /, **kwargs: Any):
        self.root = root
        self.append_pointer = append_pointer

    def __copy__(self) -> NodeTree:
        return self.__class__(self.root, self.append_pointer)
    
    def __deepcopy__(self, memo=None) -> NodeTree:
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        return self.__class__(new_root, new_pointer)

    def __replace__(self, /, **changes):
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        return self.__class__(new_root, new_pointer)

    def append(self, node: Node | NodeTree) -> None:
        """Modify the tree by appending a node to the end."""
        if isinstance(node, NodeTree):
            new_root, new_pointer = _copy_tree(node.root, node.append_pointer)
            self.append_pointer.add_child(new_root)
            self.append_pointer = new_pointer
            return

        self.append_pointer.add_child(node)
        self.append_pointer = node

    def render(self, *args, **kwargs) -> Generator[str]:
        raise NotImplementedError("Subclasses must implement render")
