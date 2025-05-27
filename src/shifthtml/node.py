import enum
from collections.abc import Sequence
from html import escape
from string.templatelib import Template
from typing import Self


from .render import render_template


class NodeType(enum.Enum):
    ELEMENT = "ELEMENT"
    TEXT = "TEXT"


class Node:
    node_type: NodeType


class TextNode(Node):
    text: str | Template

    def __init__(self, text: str | Template):
        self.text = text
        self.node_type = NodeType.TEXT

    def render(self):
        if isinstance(self.text, Template):
            text = render_template(self.text)
        else:
            text = self.text

        return escape(text)


class ElementNode(Node):
    tag: str
    children: list[Node]
    attributes: dict[str, str | Template]

    def __init__(
        self,
        tag: str,
        attributes: dict[str, str | Template] | None,
        children: Sequence[Node] | Node | None,
    ):
        self.tag = tag
        if attributes is None:
            attributes = {}
        self.attributes = attributes

        if children is None:
            children = []
        elif isinstance(children, Node):
            children = [children]
        else:
            children = list(children)

        self.children = children

        self.node_type = NodeType.ELEMENT

    def __rshift__(self, other: Sequence[Node] | Node | str | Template) -> Self:
        match other:
            case Node():
                self.children.append(other)
            case str() | Template():
                self.children.append(TextNode(other))
            case _:
                self.children.extend(other)

        return self

    def render(self) -> str:
        parts = []
        if self.attributes:
            parts.append(f"<{self.tag}")

            for attr, value in self.attributes.items():
                # TODO: escape attribute names
                if isinstance(value, Template):
                    rendered_value = render_template(value)
                else:
                    rendered_value = value

                rendered_value = escape(rendered_value, quote=True)

                parts.append(f' {attr}="{rendered_value}"')

            parts.append(">")
        else:
            parts.append(f"<{self.tag}>")

        for child in self.children:
            parts.append(child.render())

        parts.append(f"</{self.tag}>")

        return "".join(parts)
