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

    def __rshift__(self, other: Node | None | TextType | NodeListType | TagDefinition) -> Self:
        print(f"Adding content to {self.tag if hasattr(self, 'tag') else 'Node'}: {other!r}")
        if self.children is None:
            raise ValueError(f"{self.tag} cannot have content")
    
        match other:
            case TagDefinition():
                resolved = other()
            case Node():
                resolved = other
            case str() | Template():
                resolved = TextNode(other)
            case list() | tuple():
                resolved = list(other)
            case None:
                resolved = None
            case _:
                raise ValueError(f"Unsupported type for >>: {type(other)}")

        if isinstance(resolved, Node):
            resolved.parent = self
            self.children.append(resolved)
        elif isinstance(resolved, list):
            for item in resolved:
                if isinstance(item, Node):
                    item_root = item._get_root()
                    if item_root.parent is not None:
                        raise ValueError(f"Node {item_root.tag} already has a parent")
                    print(f"Adding child {item_root.tag} to {self.tag}")
                    item_root.parent = self
                    self.children.append(item_root)

        return resolved

    def _get_root(self) -> Node:
        root = self
        while root.parent is not None:
            root = root.parent

        return root


class TagDefinition[T]:
    tag: str
    node_class: T

    def __init__(self, tag: str, node_class: T):
        self.tag = tag
        self.node_class = node_class

    def __repr__(self):
        return f"TagDefinition({self.tag!r})"

    def __call__(self, *args, **kwds) -> T:
        return self.node_class(self.tag, kwds, args or None)

    def __rshift__(self, other: NodeType | TagDefinition) -> T:
        if isinstance(other, TagDefinition):
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
        print(f"Rendering TextNode with text: {self.text!r}")
        if isinstance(self.text, Template):
            yield from render_template(self.text)
        else:
            yield self.text


class ElementNode(Node):
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
        return f"ElementNode({self.tag!r}, {self.attributes!r}, {len(self.children)} children)"

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
        print(f"Rendering {self.tag} with attributes {self.attributes} and {len(self.children)} children")
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


class VoidElementNode(ElementNode):
    tag: str
    attributes: dict[str, str | Template]

    def __init__(
        self,
        tag: str,
        attributes: dict[str, str | Template] | None,
    ):
        super().__init__()

        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes

    def __repr__(self):
        return f"VoidElementNode({self.tag!r}, {self.attributes!r})"

    def render(self) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield ' '  # space before each attribute
                yield from self._render_attribute(key, value)

            yield " />"
        else:
            yield f"<{self.tag} />"
