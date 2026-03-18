"""
Abstract base classes for HTML nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Iterator
from string.templatelib import Template


class Node(metaclass=ABCMeta):
    """
    Abstract base class for nodes in a tree structure.

    Different types of nodes are supported, analogous to Document Object Model (DOM)
    nodes, such as document, element, text, comment nodes, etc.

    Nodes are initially "floating" without parent, children, or document.
    They are added to a tree via `append_child`, which sets up parent/child/document
    relationships. Adding an existing node elsewhere will raise an error.
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
        """Iterate depth-first over this node and all descendants."""
        yield self
        for child in self.children:
            yield from iter(child)

    def append_child(self, child: Node) -> None:
        """Add a child node to this node."""
        if child is self:
            raise ValueError("Can't make a node a child of itself")

        if not isinstance(child, Node):
            raise ValueError(f"Node can only contain other nodes. Unexpected type {child.__class__.__name__!r}")

        if child.parent_node is not None:
            raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent_node!r}")

        child.parent_node = self
        child._document = self._document
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


class DocumentFragment(Node):
    """
    An HTML Document Fragment, somewhere between a DOM Document and DocumentFragment.
    """

    parent_node: None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document = self

    def create_element(self, tag_name: str, attributes: dict[str, str | Template] | None = None) -> Element:
        node = Element(tag_name, attributes)
        node._document = self
        return node

    def create_text_node(self, content: str) -> Text:
        node = Text(content)
        node._document = self
        return node

    def create_comment(self, content: str) -> Comment:
        node = Comment(content)
        node._document = self
        return node

    def render(self, *args, **kwargs) -> Generator[str]:
        for child in self.children:
            yield from child.render(*args, **kwargs)


class Element(Node):
    """
    An HTML Element Node, analogous to DOM HTMLElement.
    """

    attributes: dict[str, str | Template]

    def __init__(self, tag_name: str, attributes: dict[str, str | Template] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tag_name = tag_name
        self.attributes = attributes or {}

    def __replace__(self, /, **changes):
        new_obj = type(self)(self._tag_name)
        new_obj.attributes = dict(self.attributes)
        new_children = changes.get("children", self.children)
        if new_children:
            for child in new_children:
                new_obj.append_child(copy.replace(child))
        return new_obj

    @property
    def tag_name(self) -> str:
        """The tag name of this element."""
        return self._tag_name


class Text(Node):
    """
    An HTML Text Node, analogous to DOM Text.
    """

    content: str | Template

    def __init__(self, content: str | Template, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def __replace__(self, /, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Text node")

    def render(self, *args, **kwargs) -> Generator[str]:
        yield self.content


class Comment(Node):
    """
    An HTML Comment Node, analogous to DOM Comment.
    """

    content: str | Template

    def __init__(self, content: str | Template, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def __replace__(self, /, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Comment node")

    def render(self, *args, **kwargs) -> Generator[str]:
        yield f"<!--{self.content}-->"
