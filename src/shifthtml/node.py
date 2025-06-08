from __future__ import annotations

import inspect
from collections.abc import Iterable, Sequence
from typing import Any, Generator, ClassVar, Iterator, Never, Self, overload

from .compat import Template
from .render import render_template


# DOM classes:
# Node -> https://developer.mozilla.org/en-US/docs/Web/API/Node
# NodeList -> https://developer.mozilla.org/en-US/docs/Web/API/NodeList
# Element -> https://developer.mozilla.org/en-US/docs/Web/API/Element
# HTMLElement -> https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement
# Text -> https://developer.mozilla.org/en-US/docs/Web/API/Text
# DocumentFragment -> https://developer.mozilla.org/en-US/docs/Web/API/DocumentFragment

# Our objects:
# Node
# NodeList -> Multiple node object, acts as a list but with a parent
# Text
# Element
# HTMLElement
# HTMLVoidElement -> No equivalent, used for void elements like <img>, <br>, etc.
# Fragment -> DocumentFragment


class Node:
    """
    A node in the document tree. Usually and HTML element or text content.

    Nodes have one parent and zero or more children. They are initialized without these,
    and then put into a tree by the shift operator (>>) which calls `add_child`.
    """

    parent: None | Node
    children: list[Node | Fragment]

    def __init__(self, *args, **kwargs):
        self.parent = None
        self.children = []

    def __rshift__(
        self,
        other: type[Node] | Node | None | str | Template | list[Node] | tuple[Node, ...],
    ) -> Node | None:
        if isinstance(other, (Node, Fragment)):
            resolved = other
        elif isinstance(other, (str, Template)):
            resolved = Text(content=other)
        elif inspect.isclass(other) and issubclass(other, Node):
            resolved = other()
        elif isinstance(other, (list, tuple)):
            resolved = NodeList()
            for item in other:
                if isinstance(item, Node):
                    item_root = item.root
                    resolved.add_child(item_root)
                elif isinstance(item, Fragment):
                    resolved.add_child(item)
                else:
                    raise ValueError(
                        f"NodeList can only contain Node or Fragment instances, got {type(item)}"
                    )
        elif other is None:
            resolved = None
        else:
            raise ValueError(f"Unsupported shift type for >>: {type(other)}")

        if resolved is not None:
            self.add_child(resolved)

        # Don't chain fragments
        if isinstance(resolved, Fragment):
            return self

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
            if child.parent is not None:
                raise ValueError(
                    f"Child {child!r} is already in the tree. Parent: {child.parent!r}"
                )
            child.parent = self
            self.children.append(child)
        elif isinstance(child, Fragment):
            self.children.append(child)
        else:
            raise ValueError(
                f"Node can only contain Node or Fragment instances, got {type(child)}"
            )

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

    def __repr__(self):
        return f"NodeList({repr(self.children)})"

    @overload
    def __getitem__(self, index: int) -> Node | Fragment: ...

    @overload
    def __getitem__(self, index: slice[Any, Any, Any]) -> list[Node | Fragment]: ...

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[Node | Fragment]:
        return iter(self.children)

    def __contains__(self, item: object) -> bool:
        return item in self.children

    def __reversed__(self) -> Iterator[Node | Fragment]:
        return reversed(self.children)

    def count(self, value: Node | Fragment) -> int:
        """Count occurrences of a value in the NodeList."""
        return self.children.count(value)

    def index(
        self, value: Node | Fragment, start: int = 0, stop: int | None = None
    ) -> int:
        if stop is None:
            return self.children.index(value, start)
        return self.children.index(value, start, stop)

    def render(self) -> Generator[str]:
        for child in self.children:
            yield from child.render()


class Text(Node):
    content: str | Template

    def __init__(
        self,
        *args,
        content: str | Template,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

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

    def render(self) -> Generator[str]:
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
                yield from child.render()

        yield f"</{self.tag}>"


class HTMLVoidElement(HTMLElement):
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
