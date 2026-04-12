from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Generator
from string.templatelib import Template

from .rendering import RenderContext, arender_string, render_string
from .tree import Fragment, Node, normalize


class Deferred(Node):
    __slots__ = ("loading", "slot_name")

    _deferred_node = True

    def __init__(
        self,
        child: Node | Fragment,
        *,
        slot_name: str,
        loading: str | Template | Node | None = None,
    ):
        super().__init__()
        if loading is not None and not isinstance(loading, str | Template):
            self.loading: str | Template | Node | None = normalize(loading)
        else:
            self.loading = loading
        self.slot_name = slot_name

        if isinstance(child, Fragment):
            self.append_child(child.root)
        elif isinstance(child, Node):
            self.append_child(child)
        else:
            raise ValueError(f"Deferred can only be initialized with a Node or Fragment, not {type(child)}")

    def __replace__(self, /, **changes):
        child = self.children[0]
        assert isinstance(child, Node)
        return type(self)(copy.replace(child), slot_name=self.slot_name, loading=self.loading)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        if ctx is not None:
            ctx._deferred.append(self)
        yield f'<div id="{self.slot_name}">'
        if self.loading is not None:
            yield from _render_loading(self.loading)
        yield "</div>"

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            ctx._deferred.append(self)
        yield f'<div id="{self.slot_name}">'
        if self.loading is not None:
            async for chunk in _arender_loading(self.loading):
                yield chunk
        yield "</div>"


def _render_loading(loading: str | Template | Node) -> Generator[str]:
    if isinstance(loading, str | Template):
        yield from render_string(loading)
    else:
        yield from loading.chunks()


async def _arender_loading(loading: str | Template | Node) -> AsyncGenerator[str]:
    if isinstance(loading, str | Template):
        async for chunk in arender_string(loading):
            yield chunk
    else:
        async for chunk in loading.achunks():
            yield chunk


def defer(
    slot_name: str,
    node: Node | Fragment,
    *,
    loading: Node | str | Template | None = None,
) -> Deferred:
    return Deferred(node, slot_name=slot_name, loading=loading)
