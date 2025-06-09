from __future__ import annotations

import inspect
from collections.abc import Generator, Sequence
from typing import Any, ClassVar, Iterator, Never, Self, overload

from .compat import Template
from .render import render_template


class Fragment:
    """
    A chunk of HTML that can be passed around and rendered.

    Fragments can be included in a node tree but they don't have a parent or children.
    """

    def __init__(self, content: Node):
        self.content = content
        self.deferred: list[DeferredNode] = []

    def __repr__(self):
        return f"Fragment({self.content!r})"

    def __str__(self):
        return self.render()

    def render(self, *, fragment: Fragment | None = None) -> str:
        return "".join(
            list(self.content.render(fragment=fragment or self))
            + list(self.render_deferred(fragment=fragment or self))
        )

    def add_deferred(self, node: DeferredNode) -> None:
        self.deferred.append(node)

    def render_deferred(self, *, fragment: Fragment | None = None) -> Generator[str]:
        while len(self.deferred) > 0:
            node = self.deferred.pop(0)
            yield from node.render_result(fragment=fragment)


class Node:
    """
    A node in the document tree. Usually an HTML element or text content.

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
        other: type[Node]
        | Node
        | None
        | str
        | Template
        | list[Node]
        | tuple[Node, ...],
    ) -> Node | None:
        if isinstance(other, (Node, Fragment)):
            resolved = other
        elif isinstance(other, (str, Template)):
            resolved = Text(content=other)
        elif inspect.isclass(other) and issubclass(other, Node):
            resolved = other()
        elif isinstance(other, (list, tuple, Generator)):
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

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
        """Render the node to a string"""
        for child in self.children:
            yield from child.render(fragment=fragment)


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

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
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


class DeferredNode(Node):
    def __init__(
        self,
        node: Node | Fragment,
        /,
        slot_name: str,
        loading: Node | Fragment | str | Template | None = None,
    ):
        super().__init__()
        self.loading = loading
        self.slot_name = slot_name
        self.add_child(node.root)

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
        # TODO: fix import cycle
        from .tags import template, slot
        if fragment is None:
            raise ValueError("defer must be used inside a fragment")

        self.id = fragment.add_deferred(self)

        element = template(shadowrootmode="open")
        element >> slot(name=self.slot_name) >> self.loading

        yield from element.render(fragment=fragment)

    def render_result(self, *, fragment: Fragment | None) -> Generator[str]:
        self.children[0].attributes["slot"] = self.slot_name
        yield from self.children[0].render(fragment=fragment)
