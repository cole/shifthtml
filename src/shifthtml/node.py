"""
Abstract base classes for HTML nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Iterator


class Node(metaclass=ABCMeta):
    """
    Abstract base class for nodes in a tree structure.

    Different types on nodes are supported, analogous to Document Object Model (DOM)
    nodes, such as document, element, text, comment nodes, etc.
    """

    parent_node: None | Node
    children: list[Node]

    def __init__(self, *args, **kwargs):
        self._document = None
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
        """Iterate over all child nodes."""
        yield from self.children

    def append_child(self, child: Node) -> None:
        """Add a child node to this node."""
        # TODO: check for ancestry loops
        # https://developer.mozilla.org/en-US/docs/Web/API/Node/appendChild
        if child is self:
            raise ValueError("Can't make a node a child of itself")

        if not isinstance(child, Node):
            raise ValueError(f"Node can only contain other nodes. Unexpected type {child.__class__.__name__!r}")

        child.parent_node = self
        self.children.append(child)

    def remove_child(self, child: Node) -> None:
        """Remove a child node from this node."""
        if child not in self.children:
            raise ValueError(f"Node {child!r} is not a child of this node {self!r}")

        self.children.remove(child)
        child.parent_node = None

    @property
    def document(self) -> DocumentFragment | None:
        """The DocumentFragment this node belongs to, or None if it is not in a tree."""
        return self._document

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

    @property
    def parent_element(self) -> None | Element:
        """The parent element of this node, or None if it has no parent or the parent is not an element."""
        if isinstance(self.parent_node, Element):
            return self.parent_node
        return None

    @abstractmethod
    def render(self, *args, **kwargs) -> Generator[str]:
        raise NotImplementedError("Subclasses must implement render")


class DocumentFragment(Node, metaclass=ABCMeta):
    """
    An HTML Document Fragment, analogous to DOM DocumentFragment.
    """

    parent_node: None | Node


class Element(Node, metaclass=ABCMeta):
    """
    An HTML Element Node, analogous to DOM HTMLElement.
    """

    attributes: dict[str, str]

    def __init__(self, tag_name: str, attributes: dict[str, str] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tag_name = tag_name
        self.attributes = attributes or {}

    @property
    def tag_name(self) -> str:
        """The tag name of this element."""
        return self._tag_name


class Text(Node):
    """
    An HTML Text Node, analogous to DOM Text.
    """

    content: str

    def __init__(self, content: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def render(self, *args, **kwargs) -> Generator[str]:
        yield self.content


class Comment(Node):
    """
    An HTML Comment Node, analogous to DOM Comment.
    """

    content: str

    def __init__(self, content: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def render(self, *args, **kwargs) -> Generator[str]:
        yield f"<!--{self.content}-->"
