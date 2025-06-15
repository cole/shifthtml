from __future__ import annotations

from collections.abc import Generator

from .protocols import DeferredNode, Node


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
