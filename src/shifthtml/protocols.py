from __future__ import annotations

from collections.abc import Generator, Sequence
from typing import ClassVar, Protocol, Self, runtime_checkable

from .compat import Template


@runtime_checkable
class Fragment(Protocol):

    def render(self, *, fragment: Fragment | None = None) -> str:
        ...

    def add_deferred(self, node: DeferredNode) -> None:
        ...

    def render_deferred(self, *, fragment: Fragment | None = None) -> Generator[str]:
        ...


@runtime_checkable
class Node(Protocol):

    parent: None | Node
    children: list[Node | Fragment]

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
        ...

    @property
    def root(self) -> Node:
        ...

    def add_child(self, child: Node | Fragment) -> None:
        ...

    def render(self, *, fragment: Fragment | None) -> Generator[str]:
        ...


@runtime_checkable
class Text(Node, Protocol):
    content: str | Template


@runtime_checkable
class Element(Node, Protocol):
    tag: ClassVar[str]
    attributes: dict[str, str | Template]

    def __matmul__(self, other: dict[str, str | Template]) -> Self:
        ...


@runtime_checkable
class DeferredNode(Node, Protocol):

    def render_result(self, *, fragment: Fragment | None) -> Generator[str]:
        ...
