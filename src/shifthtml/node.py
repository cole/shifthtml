from __future__ import annotations

import types
from collections.abc import Iterable, Sequence
from string.templatelib import Template
from typing import Generator, ClassVar, Never, Protocol, Self, runtime_checkable

from .render import render_template


# DOM classes:
# Node -> https://developer.mozilla.org/en-US/docs/Web/API/Node
# NodeList -> https://developer.mozilla.org/en-US/docs/Web/API/NodeList
# Element -> https://developer.mozilla.org/en-US/docs/Web/API/Element
# HTMLElement -> https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement
# Text -> https://developer.mozilla.org/en-US/docs/Web/API/Text
# DocumentFragment -> https://developer.mozilla.org/en-US/docs/Web/API/DocumentFragment

# Our objects:
# Tag -> No equivalent, used for HTMLElement creation
# Node
# NodeList -> Multiple node object, acts as a list but with a parent
# Text
# Element
# HTMLElement
# HTMLVoidElement -> No equivalent, used for void elements like <img>, <br>, etc.
# Fragment -> DocumentFragment


class Node:
    parent: None | Node
    children: None | list[Node]

    def __init__(
        self, parent: None | Node, children: None | list[Node], *args, **kwargs
    ):
        self.parent = parent
        self.children = children or []

    def __rshift__(
        self,
        other: Tag
        | Node
        | None
        | str
        | Template
        | list[Node]
        | tuple[Node, ...],
    ) -> Self:
        if isinstance(other, Tag):
            resolved = other(self, [])
        elif isinstance(other, (Node, Fragment)):
            resolved = other
        elif isinstance(other, (str, Template)):
            resolved = Text(self, None, content=other)
        elif isinstance(other, (list, tuple)):
            resolved = NodeList(self, other)
        elif other is None:
            resolved = None
        else:
            raise ValueError(f"Unsupported shift type for >>: {type(other)}")

        # Don't chain fragments
        if isinstance(resolved, Fragment):
            return self
        elif resolved:
            self.add_child(resolved)

        return resolved

    @property
    def root(self) -> Node:
        root = self
        while root.parent is not None:
            root = root.parent

        return root

    def add_child(self, child: Node | Fragment) -> None:
        """Add a child node or fragment to this node."""
        if isinstance(child, Node):
            if child.parent and child.parent is self:
                return

            if child.parent is not None:
                raise ValueError(
                    f"Cannot node {child!r} that already has a parent: {child.parent!r}"
                )
            child.parent = self
            self.children.append(child)
        elif isinstance(child, Fragment):
            self.children.append(child)

    def render(self) -> Generator[str]:
        """Render the node to a string."""
        raise NotImplementedError("Subclasses must implement render method")


class Fragment:
    """
    A chunk of HTML that can be passed around and rendered.

    Fragments can be included in a node tree but they don't have a parent or children.
    """

    def __init__(self, content: Node):
        self.content = content

    def __repr__(self):
        return f"Fragment({self.content!r})"

    def render(self) -> str:
        return "".join(self.content.render())

    def __str__(self):
        return self.render()


class NodeList(Node, Sequence):
    """A list of nodes with a position in the tree."""

    def __init__(
        self,
        parent: None | Node,
        children: Iterable[Node | Fragment],
    ):
        super().__init__(parent, [])

        for child in children:
            if isinstance(child, Node):
                child_root = child.root
                self.add_child(child_root)
            elif isinstance(child, Fragment):
                self.add_child(child)
            else:
                raise ValueError(
                    f"NodeList can only contain Node or Fragment instances, got {type(child)}"
                )

    def __repr__(self):
        return f"NodeList({repr(self.children)})"

    def __getitem__(self, index: int) -> Node | Fragment:
        return self.children[index]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterable[Node | Fragment]:
        return iter(self.children)

    def __contains__(self, item: Node | Fragment) -> bool:
        return item in self.children

    def __reversed__(self) -> Iterable[Node | Fragment]:
        return reversed(self.children)

    def count(self, value: Node | Fragment) -> int:
        """Count occurrences of a value in the NodeList."""
        return self.children.count(value)

    def index(
        self, value: Node | Fragment, start: int = 0, stop: int | None = None
    ) -> int:
        return self.children.index(value, start, stop)

    def render(self) -> Generator[str]:
        for child in self.children:
            yield from child.render()


class Text(Node):
    content: str | Template

    def __init__(
        self,
        parent: None | Node,
        children: None | list[Node],
        *,
        content: str | Template,
    ):
        super().__init__(parent, None)

        self.content = content

    def __repr__(self):
        return f"Text({self.content!r})"

    def add_child(self, child: Node | Fragment) -> Never:
        raise ValueError("Text nodes cannot have children")

    def render(self) -> Generator[str]:
        if isinstance(self.content, Template):
            yield from render_template(self.content)
        else:
            yield self.content



class ElementMeta(type):
    def __new__(mcls, name, bases, attrs, tag: str | None = None):
        cls = super().__new__(mcls, name, bases, attrs)
        cls.tag = tag

        return cls
    

class Element(Node):
    tag: str
    attributes: dict[str, str | Template]

    def __init__(
        self,
        parent: None | Node,
        children: None | list[Node],
        *,
        tag: str,
        attributes: dict[str, str | Template] | None = None,
    ):
        super().__init__(parent, children or [])

        self.tag = tag
        self.attributes = attributes or {}

    def __repr__(self):
        return f"{type(self)}({self.tag!r}, {self.attributes!r})"


class HTMLElement(Element):

    def _render_attribute(self, key: str, value: str | Template) -> Generator[str]:
        # Special case for the reserved word "class"
        if key == "classname":
            yield "class"
        else:
            yield key

        yield '="'

        if isinstance(value, Template):
            yield from render_template(value)
        else:
            yield value

        yield '"'

    def render(self) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield " "  # space before each attribute
                yield from self._render_attribute(key, value)

            yield ">"
        else:
            yield f"<{self.tag}>"

        if self.children:
            for child in self.children:
                yield from child.render()

        yield f"</{self.tag}>"


class HTMLVoidElement(HTMLElement):
    def __init__(
        self,
        parent: None | Node,
        children: None | list[Node],
        *,
        tag: str,
        attributes: dict[str, str | Template] | None = None,
    ):
        if children:
            raise ValueError(f"HTMLVoidElement ({tag}) cannot have children")

        super().__init__(parent, children, tag=tag, attributes=attributes)

    def __repr__(self):
        return f"HTMLVoidElement({self.tag!r}, {self.attributes!r})"

    def __rshift__(self, other):
        raise ValueError(f"Cannot add children to a VoidElement ({self.tag})")

    def render(self) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield " "  # space before each attribute
                yield from self._render_attribute(key, value)

            yield " />"
        else:
            yield f"<{self.tag} />"


class Tag[T: HTMLElement]:
    """
    An HTML tag. Instances are used with the shift operator (>>) to create Node instances.
    """

    tag: str
    element_type: T

    def __init__(self, tag: str, void: bool = False):
        self.tag = tag
        if void:
            self.element_type = HTMLVoidElement
        else:
            self.element_type = HTMLElement

    def __repr__(self):
        return f"Tag({self.tag!r})"

    def __call__(
            self,
            parent: None | Node = None,
            children: None | list[Node] = None,
    ):
        return self.element_type(parent, children, tag=self.tag)

    def __rshift__(
        self, other: Node | list[Node] | tuple[Node, ...] | None | str | Template | Tag
    ) -> T:
        instance = self(None, [])
        return instance >> other
