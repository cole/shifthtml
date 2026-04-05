"""Top-level rendering API.

This module owns all output concerns: plugin dispatch, context management,
streaming, and buffering. Tree types stay focused on structure.

Node dispatch is polymorphic: each node type implements _stream()/_astream()
methods. This module never imports element types directly.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Generator, Mapping
from html import escape
from string.templatelib import Interpolation, Template
from typing import Any, Literal, cast

import anyio

from .errors import RenderLimitExceeded
from .plugin import Plugin, RenderContext, registered_plugins
from .tree import TreeNode, _render_vars

# -- Low-level string / tag helpers --


def _convert(value: object, conversion: Literal["a", "r", "s"] | None) -> str:
    if conversion == "a":
        return ascii(value)
    if conversion == "r":
        return repr(value)
    return str(value)


def _needs_escape(value: str, quote: bool = False) -> bool:
    """Check if a string contains characters that need HTML escaping."""
    if "&" in value or "<" in value or ">" in value:
        return True
    return quote and ('"' in value or "'" in value)


def render_string(value: str | Template, quote: bool = False) -> Generator[str]:
    if isinstance(value, Template):
        for item in value:
            match item:
                case str() as s:
                    yield s
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        v = v()
                    if hasattr(v, "_stream"):
                        yield "".join(v._stream())
                    elif hasattr(v, "root"):
                        yield "".join(v.root._stream())
                    else:
                        v = _convert(v, conversion)
                        v = format(v, format_spec)
                        yield escape(v, quote=quote) if _needs_escape(v, quote) else v
    else:
        yield escape(value, quote=quote) if _needs_escape(value, quote) else value


async def arender_string(value: str | Template, quote: bool = False) -> AsyncGenerator[str]:
    if isinstance(value, Template):
        for item in value:
            match item:
                case str() as s:
                    yield s
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        result = v()
                        if inspect.isawaitable(result):
                            v = await result
                        else:
                            v = result
                    if hasattr(v, "_stream"):
                        yield "".join(v._stream())
                    elif hasattr(v, "root"):
                        yield "".join(v.root._stream())
                    else:
                        v = _convert(v, conversion)
                        v = format(v, format_spec)
                        yield escape(v, quote=quote) if _needs_escape(v, quote) else v
    else:
        yield escape(value, quote=quote) if _needs_escape(value, quote) else value


def render_open_tag(tag: str, attributes: Mapping[str, object], void: bool = False) -> str:
    parts: list[str] = [f"<{tag}"]
    for key, value in attributes.items():
        if value is None or value is False:
            continue
        if value is True:
            parts.append(f" {key}")
            continue
        if isinstance(value, str):
            if "&" in value or "<" in value or ">" in value or '"' in value or "'" in value:
                value = escape(value, quote=True)
            parts.append(f' {key}="{value}"')
        elif isinstance(value, set | list | tuple):
            rendered_value = " ".join(
                "".join(render_string(v if isinstance(v, Template) else str(v), quote=True)) for v in value if v
            )
            parts.append(f' {key}="{rendered_value}"')
        elif isinstance(value, Template):
            rendered_value = "".join(render_string(value, quote=True))
            parts.append(f' {key}="{rendered_value}"')
        else:
            sv = str(value)
            if "&" in sv or "<" in sv or ">" in sv or '"' in sv or "'" in sv:
                sv = escape(sv, quote=True)
            parts.append(f' {key}="{sv}"')
    parts.append(" />" if void else ">")
    return "".join(parts)


_DEFAULT_MAX_DEPTH = 100


def _extract_root(html: object) -> TreeNode:
    """Extract the root TreeNode from a Node or Fragment-like object."""
    root = html.root if hasattr(html, "root") else html
    assert isinstance(root, TreeNode)
    return root


# -- Compatibility wrapper --


def stream_node(node: TreeNode, ctx: RenderContext | None = None) -> Generator[str]:
    """Render a single node to HTML chunks (compat wrapper)."""
    yield from node._stream(ctx)


# -- RenderContext dispatch (with plugin pipeline) --


def _render_node(node: TreeNode, ctx: RenderContext) -> Generator[str]:
    """Render a node through the full plugin pipeline."""
    ctx._node_count += 1
    if ctx.max_nodes is not None and ctx._node_count > ctx.max_nodes:
        raise RenderLimitExceeded(f"Exceeded max node count ({ctx.max_nodes})")
    stream = _stream_fn(ctx)
    for plugin in ctx.plugins:
        result = plugin.pre_render_node(node, stream, ctx)
        if result is not None:
            yield from result
            yield from ctx._post_render_node(node)
            return

    yield from node._stream(ctx)
    yield from ctx._post_render_node(node)


async def _arender_node(node: TreeNode, ctx: RenderContext) -> AsyncGenerator[str]:
    """Render a node through the full async plugin pipeline."""
    ctx._node_count += 1
    if ctx.max_nodes is not None and ctx._node_count > ctx.max_nodes:
        raise RenderLimitExceeded(f"Exceeded max node count ({ctx.max_nodes})")
    async_fn = _astream_fn(ctx)
    sync_fn = _stream_fn(ctx)
    for plugin in ctx.plugins:
        ahook = getattr(plugin, "apre_render_node", None)
        result = ahook(node, async_fn, ctx) if ahook else plugin.pre_render_node(node, sync_fn, ctx)

        if result is not None:
            if isinstance(result, AsyncGenerator):
                async for chunk in result:
                    yield chunk
            else:
                for chunk in result:
                    yield chunk
            async for chunk in ctx._apost_render_node(node):
                yield chunk
            return

    async for chunk in node._astream(ctx):
        yield chunk
    async for chunk in ctx._apost_render_node(node):
        yield chunk


def _stream_fn(ctx: RenderContext):
    """Create a stream callable that renders a node's own markup."""

    def stream(node: TreeNode) -> Generator[str]:
        yield from node._stream(ctx)

    return stream


def _astream_fn(ctx: RenderContext):
    """Create an async stream callable that renders a node's own markup."""

    async def astream(node: TreeNode) -> AsyncGenerator[str]:
        async for chunk in node._astream(ctx):
            yield chunk

    return astream


# -- Public API --


def render(
    html: object,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    max_nodes: int | None = None,
) -> str:
    """Render a node tree (or compiled Template) to an HTML string."""
    _render_vars.set(args or {})
    if isinstance(html, Template):
        return "".join(render_string(html))
    root = _extract_root(html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if resolved_plugins:
        return "".join(stream(html, args=args, plugins=plugins, max_depth=max_depth, max_nodes=max_nodes))

    ctx = RenderContext(plugins=(), max_depth=max_depth, max_nodes=max_nodes)
    return "".join(_render_node(root, ctx))


def stream(
    html: object,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    max_nodes: int | None = None,
) -> Generator[str]:
    """Render a node tree (or compiled Template) as a stream of HTML chunks."""
    _render_vars.set(args or {})
    if isinstance(html, Template):
        yield from render_string(html)
        return
    root = _extract_root(html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if resolved_plugins:
        ctx = RenderContext(plugins=resolved_plugins, max_depth=max_depth, max_nodes=max_nodes)
        yield from ctx.pre_render_all()
        yield from _stream_root(root, ctx)
    else:
        yield from root._stream()


def _stream_root(root: TreeNode, ctx: RenderContext) -> Generator[str]:
    """Render the root node with plugin dispatch."""
    stream = _stream_fn(ctx)
    for plugin in ctx.plugins:
        result = plugin.pre_render_node(root, stream, ctx)
        if result is not None:
            yield from result
            yield from ctx._post_render_node(root)
            yield from ctx.post_render_all()
            return

    if hasattr(root, "tag") and not getattr(root, "void", False):
        el = cast(Any, root)
        tag = el.tag
        attrs = el._render_attrs()
        if el.doctype:
            yield el.doctype
        yield render_open_tag(tag, attrs)
        yield from stream_children(root.children, ctx)
        yield from ctx.post_render_all()
        yield f"</{tag}>"
    else:
        yield from root._stream(ctx)
        yield from ctx.post_render_all()
    yield from ctx._post_render_node(root)


async def astream(
    html: object,
    *,
    args: dict[str, object] | None = None,
    plugins: tuple[Plugin, ...] | None = None,
    min_chunk_size: int | None = 4096,
    cancel_scope: anyio.CancelScope | None = None,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    max_nodes: int | None = None,
) -> AsyncGenerator[str]:
    """Render a node tree (or compiled Template) as an async stream of HTML chunks."""
    _render_vars.set(args or {})
    if isinstance(html, Template):
        async for chunk in arender_string(html):
            yield chunk
        return
    if min_chunk_size is None:
        async for chunk in _astream_unbuffered(
            html, plugins=plugins, cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
        ):
            yield chunk
        return

    buf: list[str] = []
    buf_size = 0
    async for chunk in _astream_unbuffered(
        html, plugins=plugins, cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
    ):
        buf.append(chunk)
        buf_size += len(chunk)
        if buf_size >= min_chunk_size:
            yield "".join(buf)
            buf.clear()
            buf_size = 0
    if buf:
        yield "".join(buf)


async def _astream_unbuffered(
    html: object,
    *,
    plugins: tuple[Plugin, ...] | None = None,
    cancel_scope: anyio.CancelScope | None = None,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    max_nodes: int | None = None,
) -> AsyncGenerator[str]:
    root = _extract_root(html)
    resolved_plugins = plugins if plugins is not None else registered_plugins()

    if resolved_plugins:
        ctx = RenderContext(
            plugins=resolved_plugins, cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
        )
        async for chunk in ctx.apre_render_all():
            yield chunk
        async for chunk in _astream_root(root, ctx):
            yield chunk
    else:
        async for chunk in root._astream():
            yield chunk


async def _astream_root(root: TreeNode, ctx: RenderContext) -> AsyncGenerator[str]:
    """Render the root node with async plugin dispatch."""
    async_fn = _astream_fn(ctx)
    sync_fn = _stream_fn(ctx)
    for plugin in ctx.plugins:
        ahook = getattr(plugin, "apre_render_node", None)
        result = ahook(root, async_fn, ctx) if ahook else plugin.pre_render_node(root, sync_fn, ctx)
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

    if hasattr(root, "tag") and not getattr(root, "void", False):
        el = cast(Any, root)
        tag = el.tag
        attrs = el._render_attrs()
        if el.doctype:
            yield el.doctype
        yield render_open_tag(tag, attrs)
        async for chunk in astream_children(root.children, ctx):
            yield chunk
        async for chunk in ctx.apost_render_all():
            yield chunk
        yield f"</{tag}>"
    else:
        async for chunk in root._astream(ctx):
            yield chunk
        async for chunk in ctx.apost_render_all():
            yield chunk
    async for chunk in ctx._apost_render_node(root):
        yield chunk


# -- Children helpers --


def stream_children(children: list, ctx: RenderContext | None = None) -> Generator[str]:
    """Render a list of children to HTML chunks."""
    for child in children:
        if isinstance(child, str | Template):
            yield from render_string(child)
        elif ctx is not None:
            yield from _render_node(child, ctx)
        else:
            yield from child._stream()


async def astream_children(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Render a list of children to async HTML chunks."""
    if len(children) > 1 and any(hasattr(child, "fn") for child in children):
        async for chunk in _astream_children_parallel(children, ctx):
            yield chunk
        return

    for child in children:
        if isinstance(child, str | Template):
            async for chunk in arender_string(child):
                yield chunk
        elif ctx is not None:
            async for chunk in _arender_node(child, ctx):
                yield chunk
        else:
            async for chunk in child._astream():
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
                results[i] = [chunk async for chunk in _arender_node(child, ctx)]
            else:
                results[i] = [chunk async for chunk in child._astream()]
        ready[i].set()

    async with anyio.create_task_group() as tg:
        for i, child in enumerate(children):
            tg.start_soon(collect, i, child)

        for i in range(len(children)):
            await ready[i].wait()
            for chunk in results[i]:
                yield chunk
