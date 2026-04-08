"""Intermediate representation types and execution for compiled templates."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from dataclasses import dataclass
from string.templatelib import Template as StdlibTemplate
from typing import Any

from .rendering import _collect_result, arender_result, arender_string, collect_string, render_result, render_string
from .tree import _resolve_var
from .types import NodeContent

# -- Intermediate representation types --


@dataclass(slots=True)
class Branch:
    """Conditional branch: resolves var at render time, picks a branch."""

    var_name: str
    if_true: list[RenderOp]
    if_false: list[RenderOp]


@dataclass(slots=True)
class Loop:
    """Iteration: resolves var at render time, calls body_fn per item."""

    var_name: str
    body_fn: Callable[[Any], NodeContent]


@dataclass(slots=True)
class LoopCollect:
    """Fast-path iteration: body_fn returns objects with _collect (Node/Fragment)."""

    var_name: str
    body_fn: Callable[[Any], Any]


@dataclass(slots=True)
class LazySlot:
    """Opaque callable evaluated at render time (escape hatch)."""

    fn: Callable[..., NodeContent]


type RenderOp = str | StdlibTemplate | Branch | Loop | LoopCollect | LazySlot


# -- Op execution --


def _exec_ops(ops: list[RenderOp], out: list[str]) -> None:
    for op in ops:
        if type(op) is str:
            out.append(op)
        elif isinstance(op, StdlibTemplate):
            collect_string(op, out)
        elif isinstance(op, LoopCollect):
            body_fn = op.body_fn
            for item in _resolve_var(op.var_name):
                body_fn(item)._collect(out)
        elif isinstance(op, Loop):
            for item in _resolve_var(op.var_name):
                _collect_result(op.body_fn(item), out)
        elif isinstance(op, Branch):
            branch = op.if_true if _resolve_var(op.var_name) else op.if_false
            _exec_ops(branch, out)
        elif isinstance(op, LazySlot):
            _collect_result(op.fn(), out)


def _stream_ops(ops: list[RenderOp]) -> Generator[str]:
    for op in ops:
        match op:
            case str() as html:
                yield html
            case StdlibTemplate() as tpl:
                yield from render_string(tpl)
            case Branch(var_name, if_true, if_false):
                branch = if_true if _resolve_var(var_name) else if_false
                yield from _stream_ops(branch)
            case LoopCollect(var_name, body_fn):
                for item in _resolve_var(var_name):
                    yield from body_fn(item)._stream()
            case Loop(var_name, body_fn):
                for item in _resolve_var(var_name):
                    yield from render_result(body_fn(item), None)
            case LazySlot(fn):
                yield from render_result(fn(), None)


async def _astream_ops(ops: list[RenderOp]) -> AsyncGenerator[str]:
    for op in ops:
        match op:
            case str() as html:
                yield html
            case StdlibTemplate() as tpl:
                async for chunk in arender_string(tpl):
                    yield chunk
            case Branch(var_name, if_true, if_false):
                branch = if_true if _resolve_var(var_name) else if_false
                async for chunk in _astream_ops(branch):
                    yield chunk
            case LoopCollect(var_name, body_fn):
                for item in _resolve_var(var_name):
                    async for chunk in body_fn(item)._astream():
                        yield chunk
            case Loop(var_name, body_fn):
                for item in _resolve_var(var_name):
                    async for chunk in arender_result(body_fn(item), None):
                        yield chunk
            case LazySlot(fn):
                async for chunk in arender_result(fn(), None):
                    yield chunk


# -- Merge utility --


def _merge_ops(ops: list[RenderOp]) -> list[RenderOp]:
    """Merge adjacent string ops and recursively merge Branch sub-lists."""
    merged: list[RenderOp] = []
    for op in ops:
        if isinstance(op, Branch):
            op = Branch(op.var_name, _merge_ops(op.if_true), _merge_ops(op.if_false))
        if isinstance(op, str) and merged and isinstance(merged[-1], str):
            merged[-1] += op
        else:
            merged.append(op)
    return merged
