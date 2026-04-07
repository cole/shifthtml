"""Compile a ShiftHTML tree into a CompiledTemplate for fast repeated rendering.

Partially evaluates the tree: static HTML and eagerly-resolved Lazy nodes
become string ops, while Var slots, conditionals, and loops become intermediate
representation ops that are evaluated at render time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

from .operations import (
    Branch,
    LazySlot,
    Loop,
    RenderOp,
    _astream_ops,
    _exec_ops,
    _merge_ops,
    _stream_ops,
)
from .tree import _render_vars


# -- CompiledTemplate --


class CompiledTemplate:
    """A compiled HTML template with variable slots and control flow."""

    __slots__ = ("_ops",)

    _ops: list[RenderOp]

    def __init__(self, ops: list[RenderOp], /):
        self._ops = ops

    def render(self, *, args: dict[str, object] | None = None) -> str:
        _render_vars.set(args or {})
        parts: list[str] = []
        _exec_ops(self._ops, parts)
        return "".join(parts)

    def stream(self, *, args: dict[str, object] | None = None) -> Generator[str]:
        _render_vars.set(args or {})
        return _stream_ops(self._ops)

    async def astream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]:
        _render_vars.set(args or {})
        async for chunk in _astream_ops(self._ops):
            yield chunk

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"CompiledTemplate({self._ops!r})"
