from string.templatelib import Template
from typing import Generator, Never, Self


from .render import render_template

class Node:
    children: None | list["Node"]


type NodeListType = list[Node] | tuple[Node, ...]
type TextType = str | Template
type NodeType = Node | None | TextType | NodeListType


class TextNode(Node):
    text: str | Template
    children: None = None

    def __init__(self, text: str | Template):
        self.text = text

    def render(self) -> Generator[str]:
        if isinstance(self.text, Template):
            yield from render_template(self.text)
        else:
            yield self.text


class ElementNode(Node):
    tag: str
    children: list[Node]
    attributes: dict[TextType, TextType]

    def __init__(
        self,
        tag: str,
        attributes: dict[TextType, TextType] | None,
        children: NodeType,
    ):
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

    def __rshift__(self, other: NodeType) -> Self:
        match other:
            case Node():
                self.children.append(other)
            case str() | Template():
                self.children.append(TextNode(other))
            case None:
                pass
            case _:
                self.children.extend(other)

        return self

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


class VoidElementNode(ElementNode):
    tag: str
    children: None
    attributes: dict[TextType, TextType]

    def __init__(
        self,
        tag: str,
        attributes: dict[TextType, TextType] | None,
        children: None,
    ):
        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes

        self.children = None

    def __rshift__(self, other: NodeType) -> Never:
        raise ValueError(f"{self.tag} cannot have content because it is a void element")

    def render(self) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield ' '  # space before each attribute
                yield from self._render_attribute(key, value)

            yield " />"
        else:
            yield f"<{self.tag} />"
