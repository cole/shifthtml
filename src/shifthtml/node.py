from __future__ import annotations
from string.templatelib import Template
from typing import Generator, Protocol, Self, runtime_checkable

from .render import render_template


class Tag[T]:
    """
    A definition for a tag that can be used to create elements.
    """

    tag: str
    node_class: T

    def __init__(self, tag: str, node_class: T):
        self.tag = tag
        self.node_class = node_class

    def __repr__(self):
        return f"Tag({self.tag!r})"

    def __call__(self, parent: None | Node = None, children: None | list[Node] = None, **kwds) -> T:
        return self.node_class(parent, children, self.tag, kwds)

    def __rshift__(
        self, other: Node | list[Node] | tuple[Node, ...] | None | str | Template | Tag
    ) -> T:
        if isinstance(other, Tag):
            other = other(None, [])
        instance = self(None, [])
        return instance >> other


@runtime_checkable
class Node(Protocol):
    parent: None | Node
    children: None | list[Node]

    def __init__(
        self, parent: None | Node, children: None | list[Node], *args, **kwargs
    ):
        self.parent = parent
        if children is not None:
            self.children = list(children)
        else:
            self.children = None

    def __rshift__(self, other: Node | None | str | Template | Tag) -> Self:
        match other:
            case Node():
                resolved = other
                if resolved.parent is not None:
                    raise ValueError("Cannot add a node that already has a parent")
                resolved.parent = self
            case Tag():
                resolved = other(self, [])
            case str() | Template():
                resolved = TextNode(self, None, other)
            case list() | tuple():
                resolved = NodeList(self, other)
            case None:
                resolved = None
            case _:
                raise ValueError(f"Unsupported type for >>: {type(other)}")

        if isinstance(resolved, Node):
            self.children.append(resolved)

        return resolved

    @property
    def root(self) -> Node:
        root = self
        while root.parent is not None:
            root = root.parent

        return root

    def render(self) -> Generator[str]:
        """Render the node to a string."""
        raise NotImplementedError("Subclasses must implement render method")


class NodeList(Node):
    """A fragment/list of nodes with a position in the tree."""

    def __init__(self, parent: None | Node, children: list[Node] | tuple[Node, ...]):
        super().__init__(parent, [])

        for child in children:
            if not isinstance(child, Node):
                raise ValueError(
                    f"NodeList can only contain Node instances, got {type(child)}"
                )
            child_root = child.root

            child_root.parent = self
            self.children.append(child_root)

    def __repr__(self):
        return f"NodeList({len(self.children)} items)"

    def render(self) -> Generator[str]:
        for child in self.children:
            yield from child.render()


class TextNode(Node):
    text: str | Template

    def __init__(
        self, parent: None | Node, children: None | list[Node], text: str | Template
    ):
        super().__init__(parent, None)

        self.text = text

    def __repr__(self):
        return f"TextNode({self.text!r})"

    def render(self) -> Generator[str]:
        if isinstance(self.text, Template):
            yield from render_template(self.text)
        else:
            yield self.text


class Element(Node):
    tag: str
    attributes: dict[str, str | Template]

    def __init__(
        self,
        parent: None | Node,
        children: None | list[Node],
        tag: str,
        attributes: dict[str, str | Template] | None,
    ):
        super().__init__(parent, children or [])

        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes

    def __repr__(self):
        return (
            f"Element({self.tag!r}, {self.attributes!r}, {len(self.children)} children)"
        )

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


class VoidElement(Element):
    tag: str
    attributes: dict[str, str | Template]

    def __init__(
        self,
        parent: None | Node,
        children: None | list[Node],
        tag: str,
        attributes: dict[str, str | Template] | None,
    ):
        if children is not None:
            raise ValueError("VoidElement cannot have children")
        super().__init__(parent, None, tag, attributes)

    def __repr__(self):
        return f"VoidElement({self.tag!r}, {self.attributes!r})"

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
