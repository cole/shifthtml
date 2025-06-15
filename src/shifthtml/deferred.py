from __future__ import annotations

from collections.abc import Generator

from .compat import Template
from .node import Node
from .protocols import Fragment

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
