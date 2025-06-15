from __future__ import annotations

from collections.abc import Generator
from typing import ClassVar, Self

from .compat import Template
from .node import Node
from .protocols import Fragment
from .render import render_template



class Element(Node):
    tag: ClassVar[str]
    attributes: dict[str, str | Template]

    def __init__(self, *args, **attributes: str | Template):
        super().__init__(*args)

        self.attributes = attributes or {}

        # handle "classname" in place of reserved word "class"
        if "classname" in self.attributes:
            self.attributes["class"] = self.attributes.pop("classname")

    def __repr__(self):
        return f"{type(self)}({self.tag!r}, {self.attributes!r})"

    def __matmul__(self, other: dict[str, str | Template]) -> Self:
        self.attributes.update(other)
        return self


class HTMLElement(Element):
    def _render_attribute(self, key: str, value: str | Template) -> str:
        if isinstance(value, Template):
            rendered_value = "".join(render_template(value))
        else:
            rendered_value = value

        return f'{key}="{rendered_value}"'

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                # space before each attribute
                yield f" {self._render_attribute(key, value)}"

            yield ">"
        else:
            yield f"<{self.tag}>"

        if self.children:
            for child in self.children:
                yield from child.render(fragment=fragment)

        yield f"</{self.tag}>"


class HTMLVoidElement(HTMLElement):
    def __repr__(self):
        return f"HTMLVoidElement({self.tag!r}, {self.attributes!r})"

    def __rshift__(self, other):
        raise ValueError(f"Cannot add children to a VoidElement ({self.tag})")

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for key, value in self.attributes.items():
                yield " "  # space before each attribute
                yield from self._render_attribute(key, value)

            yield " />"
        else:
            yield f"<{self.tag} />"
