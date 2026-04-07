from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Generator
from string.templatelib import Template

from .element import ContentNode, Fragment, _wrap_content
from .plugin import RenderContext, register
from .rendering import _arender_node, _render_node, arender_string, render_string
from .tree import Node


class Deferred(ContentNode):
    __slots__ = ("loading", "slot_name")

    def __init__(
        self,
        child: Node | Fragment,
        *,
        slot_name: str,
        loading: str | Template | Node | None = None,
    ):
        super().__init__()
        if loading is not None and not isinstance(loading, str | Template):
            self.loading: str | Template | Node | None = _wrap_content(loading)
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


def _render_loading(loading: str | Template | Node, stream) -> Generator[str]:
    if isinstance(loading, str | Template):
        yield from render_string(loading)
    else:
        yield from stream(loading)


async def _arender_loading(loading: str | Template | Node, astream) -> AsyncGenerator[str]:
    if isinstance(loading, str | Template):
        async for chunk in arender_string(loading):
            yield chunk
    else:
        async for chunk in astream(loading):
            yield chunk


class DeferPlugin:
    def __call__(
        self,
        slot_name: str,
        node: Node | Fragment,
        *,
        loading: Node | str | Template | None = None,
    ) -> Deferred:
        register(self)
        return Deferred(node, slot_name=slot_name, loading=loading)

    def pre_render_node(self, node: Node, stream, ctx: RenderContext) -> Generator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._render_placeholder(node, stream)

    def _render_placeholder(self, node: Deferred, stream) -> Generator[str]:
        yield f'<div id="{node.slot_name}">'
        if node.loading is not None:
            yield from _render_loading(node.loading, stream)
        yield "</div>"

    def post_render(self, ctx: RenderContext) -> Generator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            node = deferred.pop(0)
            child = node.children[0]
            yield f'<shift-update action="replace" target="{node.slot_name}"><template>'
            yield from _render_node(child, ctx)
            yield "</template><shift-done></shift-done></shift-update>"

    def apre_render_node(self, node: Node, astream, ctx: RenderContext) -> AsyncGenerator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._arender_placeholder(node, astream)

    async def _arender_placeholder(self, node: Deferred, astream) -> AsyncGenerator[str]:
        yield f'<div id="{node.slot_name}">'
        if node.loading is not None:
            async for chunk in _arender_loading(node.loading, astream):
                yield chunk
        yield "</div>"

    async def apost_render(self, ctx: RenderContext) -> AsyncGenerator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            if ctx.cancel_scope is not None and ctx.cancel_scope.cancel_called:
                return
            node = deferred.pop(0)
            child = node.children[0]
            yield f'<shift-update action="replace" target="{node.slot_name}"><template>'
            async for chunk in _arender_node(child, ctx):
                yield chunk
            yield "</template><shift-done></shift-done></shift-update>"


defer = DeferPlugin()
