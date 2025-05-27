from __future__ import annotations
from string.templatelib import Template
from typing import Generator, Self

from .render import render_template

class Node:
    parent: None | Node
    children: None | list[Node]

    def __init__(self):
        self.parent = None
        self.children = None

    def __rshift__(self, other: Node | None | TextType | NodeListType | Tag) -> Self:
        if self.children is None:
            raise ValueError(f"{self.tag} cannot have content")
    
        match other:
            case Tag():
                resolved = other()
            case Node():
                resolved = other
            case str() | Template():
                resolved = TextNode(other)
            case list() | tuple():
                resolved = NodeList(other)
            case None:
                resolved = None
            case _:
                raise ValueError(f"Unsupported type for >>: {type(other)}")

        if isinstance(resolved, Node):
            resolved.parent = self
            self.children.append(resolved)

        return resolved

    @property
    def root(self) -> Node:
        root = self
        while root.parent is not None:
            root = root.parent

        return root


class NodeList(Node):
    """A fragment/list of nodes with a position in the tree."""

    def __init__(
        self,
        children: list[Node] | tuple[Node, ...]
    ):
        super().__init__()
        self.children = []

        for child in children:
            if not isinstance(child, Node):
                raise ValueError(f"NodeList can only contain Node instances, got {type(child)}")
            child_root = child.root

            child_root.parent = self
            self.children.append(child_root)

    def __repr__(self):
        return f"NodeList({len(self.children)} items)"
    
    def render(self) -> Generator[str]:
        for child in self.children:
            yield from child.render()


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

    def __call__(self, *args, **kwds) -> T:
        return self.node_class(self.tag, kwds, args or None)

    def __rshift__(self, other: NodeType | Tag) -> T:
        if isinstance(other, Tag):
            other = other()
        instance = self()
        return instance >> other


type NodeListType = list[Node] | tuple[Node, ...]
type TextType = str | Template
type NodeType = Node | None | TextType | NodeListType


class TextNode(Node):
    text: str | Template

    def __init__(self, text: str | Template):
        super().__init__()
    
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
        tag: str,
        attributes: dict[str, str | Template] | None,
        children: NodeType,
    ):
        super().__init__()

        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes

        if children is None:
            children = []
        elif isinstance(children, Node):
            children = [children]
        elif isinstance(children, (str, Template)):
            children = [TextNode(children)]
        else:
            children = list(children)

        self.children = children

    def __repr__(self):
        return f"Element({self.tag!r}, {self.attributes!r}, {len(self.children)} children)"

    def _render_attribute(self, key: TextType, value: TextType) -> Generator[str]:
        # Special case for the reserved word "class"
        if key == 'classname':
            yield 'class'
        elif isinstance(key, Template):
            yield from render_template(key)
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
                yield ' '  # space before each attribute
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
        tag: str,
        attributes: dict[str, str | Template] | None,
        children: None,
    ):
        super().__init__(tag, attributes, children)

        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes
        self.children = None

    def __repr__(self):
        return f"VoidElement({self.tag!r}, {self.attributes!r})"

    def render(self) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield ' '  # space before each attribute
                yield from self._render_attribute(key, value)

            yield " />"
        else:
            yield f"<{self.tag} />"
