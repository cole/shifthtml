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
from typing import Literal

import anyio

from .errors import RenderLimitExceeded
from .plugin import AStreamFn, RenderContext, StreamFn
from .tree import Node
from .types import Renderable, is_async_content_fn, is_sync_content_fn

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
                    if isinstance(v, Renderable):
                        yield "".join(v._stream())
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
                    if isinstance(v, Renderable):
                        yield "".join(v._stream())
                    else:
                        v = _convert(v, conversion)
                        v = format(v, format_spec)
                        yield escape(v, quote=quote) if _needs_escape(v, quote) else v
    else:
        yield escape(value, quote=quote) if _needs_escape(value, quote) else value


def render_open_tag(tag: str, attributes: Mapping[str, object], void: bool = False) -> str:
    if not attributes:
        return f"<{tag} />" if void else f"<{tag}>"
    # Fast path: single string attribute (most common case)
    if len(attributes) == 1:
        key = next(iter(attributes))
        value = attributes[key]
        if isinstance(value, str):
            if "&" in value or "<" in value or ">" in value or '"' in value or "'" in value:
                value = escape(value, quote=True)
            return f'<{tag} {key}="{value}" />' if void else f'<{tag} {key}="{value}">'
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


# -- Callable result helpers --


def render_result(result: object, ctx: RenderContext | None) -> Generator[str]:
    """Render the return value of a Lazy/Async callable."""
    if result is None or result is False:
        return
    if isinstance(result, str | Template):
        yield from render_string(result)
        return
    if isinstance(result, Node):
        if ctx is not None:
            yield from _render_node(result, ctx)
        else:
            yield from result._stream()
        return
    if isinstance(result, Renderable):
        yield from result._stream(ctx)
        return
    if isinstance(result, tuple | list):
        for item in result:
            yield from render_result(item, ctx)
        return
    if is_sync_content_fn(result):
        yield from render_result(result(), ctx)
        return
    raise ValueError(f"Unsupported content type: {type(result)}")


async def arender_result(result: object, ctx: RenderContext | None) -> AsyncGenerator[str]:
    """Async render the return value of a Lazy/Async callable."""
    if result is None or result is False:
        return
    if isinstance(result, str | Template):
        async for chunk in arender_string(result):
            yield chunk
        return
    if isinstance(result, Node):
        if ctx is not None:
            async for chunk in _arender_node(result, ctx):
                yield chunk
        else:
            async for chunk in result._astream():
                yield chunk
        return
    if isinstance(result, Renderable):
        async for chunk in result._astream(ctx):
            yield chunk
        return
    if isinstance(result, tuple | list):
        for item in result:
            async for chunk in arender_result(item, ctx):
                yield chunk
        return
    if is_async_content_fn(result):
        async for chunk in arender_result(await result(), ctx):
            yield chunk
        return
    if is_sync_content_fn(result):
        async for chunk in arender_result(result(), ctx):
            yield chunk
        return
    raise ValueError(f"Unsupported content type: {type(result)}")


# -- RenderContext dispatch (with plugin pipeline) --


def _render_node(node: Node, ctx: RenderContext) -> Generator[str]:
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


async def _arender_node(node: Node, ctx: RenderContext) -> AsyncGenerator[str]:
    """Render a node through the full async plugin pipeline."""
    ctx._node_count += 1
    if ctx.max_nodes is not None and ctx._node_count > ctx.max_nodes:
        raise RenderLimitExceeded(f"Exceeded max node count ({ctx.max_nodes})")
    async_fn = _astream_fn(ctx)
    sync_fn = _stream_fn(ctx)
    for plugin in ctx.plugins:
        ahook = getattr(plugin, "apre_render_node", None)
        if ahook is not None:
            aresult: AsyncGenerator[str] | None = ahook(node, async_fn, ctx)
            if aresult is not None:
                async for chunk in aresult:
                    yield chunk
                async for chunk in ctx._apost_render_node(node):
                    yield chunk
                return
        else:
            sresult = plugin.pre_render_node(node, sync_fn, ctx)
            if sresult is not None:
                for chunk in sresult:
                    yield chunk
                async for chunk in ctx._apost_render_node(node):
                    yield chunk
                return

    async for chunk in node._astream(ctx):
        yield chunk
    async for chunk in ctx._apost_render_node(node):
        yield chunk


def _stream_fn(ctx: RenderContext) -> StreamFn:
    """Create a stream callable that renders a node's own markup."""

    def stream(node: Node) -> Generator[str]:
        yield from node._stream(ctx)

    return stream


def _astream_fn(ctx: RenderContext) -> AStreamFn:
    """Create an async stream callable that renders a node's own markup."""

    async def astream(node: Node) -> AsyncGenerator[str]:
        async for chunk in node._astream(ctx):
            yield chunk

    return astream


# -- Children helpers --


def _collect_children(children: list, buf: list[str]) -> None:
    """Collect rendered HTML for children into a buffer (non-generator fast path)."""
    for child in children:
        if type(child) is str:
            if "&" in child or "<" in child or ">" in child:
                buf.append(escape(child))
            else:
                buf.append(child)
        elif isinstance(child, Template):
            buf.extend(render_string(child))
        else:
            child._collect(buf)


def _collect_result(result: object, buf: list[str]) -> None:
    """Collect the return value of a Lazy callable into a buffer."""
    if result is None or result is False:
        return
    if isinstance(result, Node):
        result._collect(buf)
        return
    if isinstance(result, str):
        buf.append(escape(result) if _needs_escape(result) else result)
        return
    if isinstance(result, tuple | list):
        for item in result:
            _collect_result(item, buf)
        return
    if isinstance(result, Renderable):
        result._collect(buf)
        return
    if isinstance(result, Template):
        buf.extend(render_string(result))
        return
    if is_sync_content_fn(result):
        _collect_result(result(), buf)
        return
    raise ValueError(f"Unsupported content type: {type(result)}")


def stream_children(children: list, ctx: RenderContext | None = None) -> Generator[str]:
    """Render a list of children to HTML chunks."""
    for child in children:
        if type(child) is str:
            if "&" in child or "<" in child or ">" in child:
                yield escape(child)
            else:
                yield child
        elif isinstance(child, Template):
            yield from render_string(child)
        elif ctx is not None:
            yield from _render_node(child, ctx)
        else:
            yield from child._stream()


async def astream_children(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Render a list of children to async HTML chunks."""
    if len(children) > 1 and any(getattr(child, "_may_block", False) for child in children):
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
        elif isinstance(child, Node):
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
