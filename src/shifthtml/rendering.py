"""Top-level rendering API.

This module owns all output concerns: plugin dispatch, context management,
streaming, and buffering. Tree types stay focused on structure.

Public API:
    render(node, *, args, plugins)   → str
    stream(node, *, args, plugins)   → Generator[str]
    astream(node, *, args, plugins)  → AsyncGenerator[str]
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from string.templatelib import Interpolation, Template

import anyio

from .element import Async, Element, Fragment, Lazy, Node, _render_vars
from .plugin import Plugin, RenderContext, registered_plugins
from .render import arender_string, render_string
from .tree import TreeNode
from .types import NodeContent


def render(
    html: Node | Fragment,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
) -> str:
    """Render a node tree to an HTML string."""
    _render_vars.set(args or {})
    frag = html if isinstance(html, Fragment) else Fragment(html, html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if not resolved_plugins:
        parts: list[str] = []
        _collect_node(frag.root, parts)
        return "".join(parts)

    return "".join(stream(html, args=args, plugins=plugins))


def stream(
    html: Node | Fragment,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
) -> Generator[str]:
    """Render a node tree as a stream of HTML chunks."""
    _render_vars.set(args or {})
    frag = html if isinstance(html, Fragment) else Fragment(html, html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if resolved_plugins:
        ctx = RenderContext(plugins=resolved_plugins)
        yield from ctx.pre_render_all()
        yield from _stream_root(frag.root, ctx)
    else:
        yield from frag.root.render_html()


def _stream_root(root: TreeNode, ctx: RenderContext) -> Generator[str]:
    """Render the root node with plugin dispatch."""
    for plugin in ctx.plugins:
        result = plugin.pre_render_node(root, ctx)
        if result is not None:
            yield from result
            yield from ctx._post_render_node(root)
            yield from ctx.post_render_all()
            return

    if isinstance(root, Element) and not root.void:
        yield from root.render_html(ctx=ctx, before_close=ctx.post_render_all)
    else:
        yield from root.render_html(ctx=ctx)
        yield from ctx.post_render_all()
    yield from ctx._post_render_node(root)


async def astream(
    html: Node | Fragment,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
    min_chunk_size: int | None = 4096,
    cancel_scope: anyio.CancelScope | None = None,
) -> AsyncGenerator[str]:
    """Render a node tree as an async stream of HTML chunks."""
    _render_vars.set(args or {})
    if min_chunk_size is None:
        async for chunk in _astream_unbuffered(html, plugins=plugins, cancel_scope=cancel_scope):
            yield chunk
        return

    buf: list[str] = []
    buf_size = 0
    async for chunk in _astream_unbuffered(html, plugins=plugins, cancel_scope=cancel_scope):
        buf.append(chunk)
        buf_size += len(chunk)
        if buf_size >= min_chunk_size:
            yield "".join(buf)
            buf.clear()
            buf_size = 0
    if buf:
        yield "".join(buf)


async def _astream_unbuffered(
    html: Node | Fragment,
    *,
    plugins: tuple[Plugin, ...] | None = None,
    cancel_scope: anyio.CancelScope | None = None,
) -> AsyncGenerator[str]:
    frag = html if isinstance(html, Fragment) else Fragment(html, html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if resolved_plugins:
        ctx = RenderContext(plugins=resolved_plugins, cancel_scope=cancel_scope)
        async for chunk in ctx.apre_render_all():
            yield chunk
        async for chunk in _astream_root(frag.root, ctx):
            yield chunk
    else:
        async for chunk in frag.root.arender_html():
            yield chunk


async def _astream_root(root: TreeNode, ctx: RenderContext) -> AsyncGenerator[str]:
    """Render the root node with async plugin dispatch."""
    for plugin in ctx.plugins:
        ahook = getattr(plugin, "apre_render_node", None)
        result = ahook(root, ctx) if ahook is not None else plugin.pre_render_node(root, ctx)
        if result is not None:
            if isinstance(result, AsyncGenerator):
                async for chunk in result:
                    yield chunk
            else:
                for chunk in result:
                    yield chunk
            async for chunk in ctx._apost_render_node(root):
                yield chunk
            async for chunk in ctx.apost_render_all():
                yield chunk
            return

    if isinstance(root, Element) and not root.void:
        async for chunk in root.arender_html(ctx=ctx, before_close=ctx.apost_render_all):
            yield chunk
    else:
        async for chunk in root.arender_html(ctx=ctx):
            yield chunk
        async for chunk in ctx.apost_render_all():
            yield chunk
    async for chunk in ctx._apost_render_node(root):
        yield chunk


# -- Children helpers (used by node render_html methods) --


def stream_children(children: list, ctx: RenderContext | None = None) -> Generator[str]:
    """Render a list of children to HTML chunks."""
    for child in children:
        if isinstance(child, str | Template):
            yield from render_string(child)
        elif ctx is not None:
            yield from ctx.render_node(child)
        else:
            yield from child.render_html()


async def astream_children(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Render a list of children to async HTML chunks."""
    # Use parallel rendering only when multiple siblings include async callables
    if len(children) > 1 and any(isinstance(child, Async | Lazy) for child in children):
        async for chunk in _astream_children_parallel(children, ctx):
            yield chunk
        return

    for child in children:
        if isinstance(child, str | Template):
            async for chunk in arender_string(child):
                yield chunk
        elif ctx is not None:
            async for chunk in ctx.arender_node(child):
                yield chunk
        else:
            async for chunk in child.arender_html():
                yield chunk


async def _astream_children_parallel(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Parallel variant for trees containing Async/Lazy sibling nodes."""
    results: list[list[str]] = [[] for _ in children]
    ready: list[anyio.Event] = [anyio.Event() for _ in children]

    async def collect(i: int, child: object) -> None:
        if isinstance(child, str | Template):
            results[i] = [chunk async for chunk in arender_string(child)]
        elif isinstance(child, TreeNode):
            if ctx is not None:
                results[i] = [chunk async for chunk in ctx.arender_node(child)]
            else:
                results[i] = [chunk async for chunk in child.arender_html()]
        ready[i].set()

    async with anyio.create_task_group() as tg:
        for i, child in enumerate(children):
            tg.start_soon(collect, i, child)

        for i in range(len(children)):
            await ready[i].wait()
            for chunk in results[i]:
                yield chunk


# -- Callable result helpers --


def render_result(result: NodeContent, ctx: RenderContext | None) -> Generator[str]:
    """Render the return value of a Lazy/Async callable."""
    if result is None:
        return
    if isinstance(result, str | Template):
        yield from render_string(result)
        return
    if isinstance(result, tuple | list):
        for item in result:
            yield from render_result(item, ctx)  # type: ignore[arg-type]  # list items are NodeContent
        return
    node = Node.factory(result)
    if ctx is not None:
        yield from ctx.render_node(node)
    else:
        yield from node.render_html()


async def arender_result(result: NodeContent, ctx: RenderContext | None) -> AsyncGenerator[str]:
    """Async render the return value of a Lazy/Async callable."""
    if result is None:
        return
    if isinstance(result, str | Template):
        async for chunk in arender_string(result):
            yield chunk
        return
    if isinstance(result, tuple | list):
        for item in result:
            async for chunk in arender_result(item, ctx):  # type: ignore[arg-type]  # list items are NodeContent
                yield chunk
        return
    node = Node.factory(result)
    if ctx is not None:
        async for chunk in ctx.arender_node(node):
            yield chunk
    else:
        async for chunk in node.arender_html():
            yield chunk


# -- Fast collect path (no generators, used by render()) --

from .render import _needs_escape, render_open_tag

_html_escape = __import__("html").escape


def _collect_string(value: str | Template, parts: list[str], quote: bool = False) -> None:
    if isinstance(value, str):
        parts.append(_html_escape(value, quote=quote) if _needs_escape(value, quote) else value)
    else:
        for item in value:
            match item:
                case str() as s:
                    parts.append(s)
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        v = v()
                    from .render import _convert

                    v = _convert(v, conversion)
                    v = format(v, format_spec)
                    parts.append(_html_escape(v, quote=quote) if _needs_escape(v, quote) else v)


def _collect_children(children: list, parts: list[str]) -> None:
    for child in children:
        if isinstance(child, str | Template):
            _collect_string(child, parts)
        else:
            _collect_node(child, parts)


def _collect_result(result: NodeContent, parts: list[str]) -> None:
    if result is None:
        return
    if isinstance(result, str | Template):
        _collect_string(result, parts)
        return
    if isinstance(result, tuple | list):
        for item in result:
            _collect_result(item, parts)  # type: ignore[arg-type]
        return
    node = Node.factory(result)
    _collect_node(node, parts)


def _collect_node(node: TreeNode, parts: list[str]) -> None:
    if isinstance(node, Element):
        if node.tag == "html":
            parts.append("<!DOCTYPE html>")
        attrs = node._render_attrs()
        if node.void:
            parts.append(render_open_tag(node.tag, attrs, void=True))
        else:
            parts.append(render_open_tag(node.tag, attrs))
            _collect_children(node.children, parts)
            parts.append(f"</{node.tag}>")
    elif isinstance(node, Lazy):
        _collect_result(node.fn(), parts)
    else:
        # Fallback for Comment, bare Node, etc.
        parts.extend(node.render_html())
