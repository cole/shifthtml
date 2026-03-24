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

    def pre_render_node(self, node: TreeNode, stream, ctx: RenderContext) -> Generator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._render_placeholder(node, stream)

    def _render_placeholder(self, node: Deferred, stream) -> Generator[str]:
        yield f'<div id="p:{node.slot_name}">'
        if node.loading is not None:
            yield from _render_loading(node.loading, stream)
        yield "</div>"

    def post_render(self, ctx: RenderContext) -> Generator[str]:
        from .rendering import _render_node

        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            node = deferred.pop(0)
            child = node.children[0]
            html = "".join(_render_node(child, ctx))
            escaped = _escape_js_template(html)
            yield f'<script>document.getElementById("p:{node.slot_name}").outerHTML=`{escaped}`</script>'

    def apre_render_node(self, node: TreeNode, astream, ctx: RenderContext) -> AsyncGenerator[str] | None:
        if not isinstance(node, Deferred):
            return None

        ctx.state.setdefault("deferred", []).append(node)
        return self._arender_placeholder(node, astream)

    async def _arender_placeholder(self, node: Deferred, astream) -> AsyncGenerator[str]:
        yield f'<div id="p:{node.slot_name}">'
        if node.loading is not None:
            async for chunk in _arender_loading(node.loading, astream):
                yield chunk
        yield "</div>"

    async def apost_render(self, ctx: RenderContext) -> AsyncGenerator[str]:
        from .rendering import _arender_node

        deferred: list[Deferred] = ctx.state.get("deferred", [])
        while deferred:
            if ctx.cancel_scope is not None and ctx.cancel_scope.cancel_called:
                return
            node = deferred.pop(0)
            child = node.children[0]
            chunks: list[str] = []
            async for chunk in _arender_node(child, ctx):
                chunks.append(chunk)
            html = "".join(chunks)
            escaped = _escape_js_template(html)
            yield f'<script>document.getElementById("p:{node.slot_name}").outerHTML=`{escaped}`</script>'


defer = DeferPlugin()
