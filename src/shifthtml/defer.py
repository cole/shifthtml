from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from string.templatelib import Template

from .element import Deferred, Element, Fragment, Node
from .plugin import RenderContext, register
from .tree import TreeNode


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

    def pre_render_node(self, node: TreeNode, ctx: RenderContext) -> Generator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._render_placeholder(node, ctx)

    def _render_placeholder(self, node: Deferred, ctx: RenderContext) -> Generator[str]:
        yield f'<template shadowrootmode="open"><slot name="{node.slot_name}">'
        if node.loading_node is not None:
            yield from ctx.render_node(node.loading_node)
        yield "</slot></template>"

    def post_render(self, ctx: RenderContext) -> Generator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            node = deferred.pop(0)
            child = node.children[0]
            if isinstance(child, Element):
                child["slot"] = node.slot_name
            yield from ctx.render_node(child)

    def apre_render_node(self, node: TreeNode, ctx: RenderContext) -> AsyncGenerator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._arender_placeholder(node, ctx)

    async def _arender_placeholder(self, node: Deferred, ctx: RenderContext) -> AsyncGenerator[str]:
        yield f'<template shadowrootmode="open"><slot name="{node.slot_name}">'
        if node.loading_node is not None:
            async for chunk in ctx.arender_node(node.loading_node):
                yield chunk
        yield "</slot></template>"

    async def apost_render(self, ctx: RenderContext) -> AsyncGenerator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            node = deferred.pop(0)
            child = node.children[0]
            if isinstance(child, Element):
                child["slot"] = node.slot_name
            async for chunk in ctx.arender_node(child):
                yield chunk


defer = DeferPlugin()
