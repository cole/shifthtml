from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from string.templatelib import Template

from .element import Deferred, Fragment, Node
from .plugin import RenderContext, register
from .render import arender_string, render_string
from .tree import TreeNode


def _escape_js_template(html: str) -> str:
    """Escape HTML for safe embedding inside a JS template literal."""
    return html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${").replace("</", "<\\/")


def _render_loading(loading: str | Template | Node, ctx: RenderContext) -> Generator[str]:
    if isinstance(loading, str | Template):
        yield from render_string(loading)
    else:
        yield from ctx.render_node(loading)


async def _arender_loading(loading: str | Template | Node, ctx: RenderContext) -> AsyncGenerator[str]:
    if isinstance(loading, str | Template):
        async for chunk in arender_string(loading):
            yield chunk
    else:
        async for chunk in ctx.arender_node(loading):
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

    def pre_render_node(self, node: TreeNode, ctx: RenderContext) -> Generator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._render_placeholder(node, ctx)

    def _render_placeholder(self, node: Deferred, ctx: RenderContext) -> Generator[str]:
        yield f'<div id="p:{node.slot_name}">'
        if node.loading is not None:
            yield from _render_loading(node.loading, ctx)
        yield "</div>"

    def post_render(self, ctx: RenderContext) -> Generator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            node = deferred.pop(0)
            child = node.children[0]
            html = "".join(ctx.render_node(child))
            escaped = _escape_js_template(html)
            yield f'<script>document.getElementById("p:{node.slot_name}").outerHTML=`{escaped}`</script>'

    def apre_render_node(self, node: TreeNode, ctx: RenderContext) -> AsyncGenerator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._arender_placeholder(node, ctx)

    async def _arender_placeholder(self, node: Deferred, ctx: RenderContext) -> AsyncGenerator[str]:
        yield f'<div id="p:{node.slot_name}">'
        if node.loading is not None:
            async for chunk in _arender_loading(node.loading, ctx):
                yield chunk
        yield "</div>"

    async def apost_render(self, ctx: RenderContext) -> AsyncGenerator[str]:
        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            if ctx.cancel_scope is not None and ctx.cancel_scope.cancel_called:
                return
            node = deferred.pop(0)
            child = node.children[0]
            chunks: list[str] = []
            async for chunk in ctx.arender_node(child):
                chunks.append(chunk)
            html = "".join(chunks)
            escaped = _escape_js_template(html)
            yield f'<script>document.getElementById("p:{node.slot_name}").outerHTML=`{escaped}`</script>'


defer = DeferPlugin()
