from __future__ import annotations

from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from typing import Any, ClassVar, Never, Self, TypeVar, overload

from .compat import Template
from .render import render_string

type NodeClassContent = type[Node] | Node | None
type NodeTextContent = str | Template
type NodeListContent = Iterable[NodeClassContent | NodeTextContent]
type NodeCallableContent = Callable[[], NodeClassContent | NodeTextContent | NodeListContent]
type NodeContent = NodeClassContent | NodeTextContent | NodeListContent | NodeCallableContent


type T = TypeVar["T"]


def _maybe_call(item: Callable[[], T] | T) -> T:
    if callable(item):
        return item()
    return item


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
        return "".join(self)

    def __iter__(self) -> Iterator[str]:
        yield from self.render()

    def add_deferred(self, node: DeferredNode) -> None:
        self.deferred.append(node)

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
        if defer_callback is None:
            defer_callback = self.add_deferred
        yield from self.content.render(defer_callback=defer_callback)
        yield from self.render_deferred()

    def render_deferred(self) -> Generator[str]:
        while len(self.deferred) > 0:
            node = self.deferred.pop(0)
            yield from node.render_result(defer_callback=self.add_deferred)


class Node:
    """
    A node in the document tree. Usually an HTML element or text content.

    Nodes have one parent and zero or more children. They are initialized without these,
    and then put into a tree by the shift operator (>>) which calls `add_child`.
    """

    parent: None | Node
    children: list[Node | Fragment]

    def __init__(self):
        self.parent = None
        self.children = []

    @classmethod
    def create(cls, contents: NodeContent) -> Node:
        if isinstance(contents, Node):
            # Assign the root, to handle chaining
            resolved = contents.root
        elif isinstance(contents, (str | Template)):
            resolved = Text(contents)
        elif contents is None:
            resolved = None
        elif isinstance(contents, Iterable):
            resolved = NodeList(contents)
        else:
            raise ValueError(f"Unsupported shift type for >>: {type(contents)}")

        return resolved

    def __rshift__(
        self,
        other: NodeContent | Fragment,
    ) -> Node | None:
        other = _maybe_call(other)

        if isinstance(other, Fragment):
            self.add_child(other)
            # Don't chain fragments
            return self

        node = Node.create(other)
        self.add_child(node)
        return node

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
                raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent!r}")
            child.parent = self
            self.children.append(child)
        elif isinstance(child, Fragment):
            self.children.append(child)
        else:
            raise ValueError(f"Node can only contain Node or Fragment instances, got {type(child)}")

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
        """Render the node to a string"""
        for child in self.children:
            yield from child.render(defer_callback=defer_callback)


class NodeList(Node, Sequence):
    """A list of nodes with a position in the tree."""

    def __init__(self, contents: NodeListContent):
        super().__init__()

        for item in contents:
            if isinstance(item, Fragment):
                self.add_child(item)
            else:
                item_node = Node.create(_maybe_call(item))
                self.add_child(item_node)

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

    def index(self, value: Node | Fragment, start: int = 0, stop: int | None = None) -> int:
        if stop is None:
            return self.children.index(value, start)
        return self.children.index(value, start, stop)


class Text(Node):
    content: str | Template

    def __init__(self, content: str | Template):
        super().__init__()

        self.content = content

    def __repr__(self):
        return f"Text({self.content!r})"

    def add_child(self, child: Node | Fragment) -> Never:
        raise ValueError("Text nodes cannot have children")

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
        yield from render_string(self.content)


class Element(Node):
    tag: ClassVar[str]
    attributes: dict[str, str | Template]

    def __init__(self, **attributes: str | Template):
        super().__init__()

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
        rendered_value = "".join(render_string(value))
        return f'{key}="{rendered_value}"'

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
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
                yield from child.render(defer_callback=defer_callback)

        yield f"</{self.tag}>"


class HTMLVoidElement(HTMLElement):
    def __repr__(self):
        return f"HTMLVoidElement({self.tag!r}, {self.attributes!r})"

    def __rshift__(self, other):
        raise ValueError(f"Cannot add children to a VoidElement ({self.tag})")

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
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
        node: Node,
        /,
        slot_name: str,
        loading: NodeContent = None,
    ):
        super().__init__()
        self.loading = loading
        self.slot_name = slot_name
        self.add_child(node.root)

    def render(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
        # Render the loading message
        defer_callback(self)
        loading_node = Node.create(self.loading)

        yield f'<template shadowrootmode="open"><slot name="{self.slot_name}">'
        yield from loading_node.render(defer_callback=defer_callback)
        yield "</slot></template>"

    def render_result(self, *, defer_callback: Callable[[Node], None] | None = None) -> Generator[str]:
        if isinstance(self.children[0], HTMLElement):
            self.children[0].attributes["slot"] = self.slot_name
        yield from self.children[0].render(defer_callback=defer_callback)
