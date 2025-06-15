from __future__ import annotations

import inspect
from collections.abc import Generator, Sequence
from typing import Any, Iterator, Never, overload

from .compat import Template
from .protocols import Fragment
from .render import render_template


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
