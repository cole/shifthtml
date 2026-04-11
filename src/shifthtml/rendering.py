"""Top-level rendering API.

This module owns all output concerns: context management, streaming,
and buffering. Tree types stay focused on structure.

Node dispatch is polymorphic: each node type implements chunks()/achunks()
methods. This module never imports element types directly.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Generator, Mapping
from dataclasses import dataclass, field
from html import escape
from string.templatelib import Interpolation, Template
from typing import TYPE_CHECKING, Any, Literal

import anyio

from .errors import RenderLimitExceeded
from .types import Renderable, is_content_fn

if TYPE_CHECKING:
    from .deferred import Deferred


@dataclass(slots=True)
class RenderContext:
    state: dict[Any, Any] = field(default_factory=dict)
    max_depth: int = 100
    max_nodes: int | None = None
    _depth: int = field(default=0, repr=False)
    _node_count: int = field(default=0, repr=False)
    _deferred: list[Deferred] = field(default_factory=list, repr=False)
    _root_node: object | None = field(default=None, repr=False)


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
                        yield "".join(v.chunks())
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
                        yield "".join(v.chunks())
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
        (key,) = attributes
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


async def arender_result(result: object, ctx: RenderContext | None) -> AsyncGenerator[str]:
    """Async render the return value of a Lazy callable."""
    if result is None or result is False:
        return
    if isinstance(result, str | Template):
        async for chunk in arender_string(result):
            yield chunk
        return
    if isinstance(result, Renderable):
        if ctx is not None:
            async for chunk in _arender_node(result, ctx):
                yield chunk
        else:
            async for chunk in result.achunks():
                yield chunk
        return
    if isinstance(result, tuple | list):
        for item in result:
            async for chunk in arender_result(item, ctx):
                yield chunk
        return
    if is_content_fn(result):
        res = result()
        if inspect.isawaitable(res):
            res = await res
        async for chunk in arender_result(res, ctx):
            yield chunk
        return
    raise ValueError(f"Unsupported content type: {type(result)}")


# -- RenderContext dispatch --


def _render_node(node: Renderable, ctx: RenderContext) -> Generator[str]:
    """Render a node through the context (tracks node count)."""
    ctx._node_count += 1
    if ctx.max_nodes is not None and ctx._node_count > ctx.max_nodes:
        raise RenderLimitExceeded(f"Exceeded max node count ({ctx.max_nodes})")
    yield from node.chunks(ctx)


async def _arender_node(node: Renderable, ctx: RenderContext) -> AsyncGenerator[str]:
    """Render a node through the async context (tracks node count)."""
    ctx._node_count += 1
    if ctx.max_nodes is not None and ctx._node_count > ctx.max_nodes:
        raise RenderLimitExceeded(f"Exceeded max node count ({ctx.max_nodes})")
    async for chunk in node.achunks(ctx):
        yield chunk


# -- Deferred flushing --


def flush_deferred(ctx: RenderContext) -> Generator[str]:
    """Flush accumulated deferred nodes as <shift-update> elements."""
    while ctx._deferred:
        node = ctx._deferred.pop(0)
        child = node.children[0]
        assert isinstance(child, Renderable)
        yield f'<shift-update action="replace" target="{node.slot_name}"><template>'
        yield from _render_node(child, ctx)
        yield "</template><shift-done></shift-done></shift-update>"


async def aflush_deferred(ctx: RenderContext) -> AsyncGenerator[str]:
    """Async flush accumulated deferred nodes as <shift-update> elements."""
    while ctx._deferred:
        node = ctx._deferred.pop(0)
        child = node.children[0]
        assert isinstance(child, Renderable)
        yield f'<shift-update action="replace" target="{node.slot_name}"><template>'
        async for chunk in _arender_node(child, ctx):
            yield chunk
        yield "</template><shift-done></shift-done></shift-update>"


# -- Children helpers --


def _collect_result(result: object, buf: list[str]) -> None:
    """Collect the return value of a Lazy callable into a buffer."""
    if result is None or result is False:
        return
    if type(result) is str:
        buf.append(escape(result) if _needs_escape(result) else result)
        return
    if type(result) is tuple or type(result) is list:
        for item in result:
            _collect_result(item, buf)
        return
    if isinstance(result, Renderable):
        buf.extend(result.chunks())
        return
    if isinstance(result, Template):
        buf.extend(render_string(result))
        return
    if is_content_fn(result):
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
            yield from child.chunks()


async def astream_children(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Render a list of children to async HTML chunks."""
    if len(children) > 1 and any(getattr(child, "_is_async", False) for child in children):
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
            async for chunk in child.achunks():
                yield chunk


async def _astream_children_parallel(children: list, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    """Parallel variant for trees containing Async/Lazy sibling nodes."""
    results: list[list[str]] = [[] for _ in children]
    ready: list[anyio.Event] = [anyio.Event() for _ in children]

    async def collect(i: int, child: object) -> None:
        if isinstance(child, str | Template):
            results[i] = [chunk async for chunk in arender_string(child)]
        elif isinstance(child, Renderable):
            if ctx is not None:
                results[i] = [chunk async for chunk in _arender_node(child, ctx)]
            else:
                results[i] = [chunk async for chunk in child.achunks()]
        ready[i].set()

    async with anyio.create_task_group() as tg:
        for i, child in enumerate(children):
            tg.start_soon(collect, i, child)

        for i in range(len(children)):
            await ready[i].wait()
            for chunk in results[i]:
                yield chunk


async def buffer_chunks(source: AsyncGenerator[str], min_size: int = 4096) -> AsyncGenerator[str]:
    """Buffer an async chunk stream, flushing when accumulated size reaches min_size."""
    buf: list[str] = []
    buf_size = 0
    async for chunk in source:
        buf.append(chunk)
        buf_size += len(chunk)
        if buf_size >= min_size:
            yield "".join(buf)
            buf.clear()
            buf_size = 0
    if buf:
        yield "".join(buf)
