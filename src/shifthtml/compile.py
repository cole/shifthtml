"""Compile a ShiftHTML tree into a CompiledTemplate for fast repeated rendering.

Walks the tree once at compile time and generates a Python function via exec().
Static HTML becomes string literals, Var slots become inline resolution code,
conditionals become if/else blocks, and loops become for loops.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator

from .codegen import compile_to_function
from .element import ContentNode, Fragment
from .tree import _render_vars


class CompiledTemplate:
    """A compiled HTML template backed by a generated Python function."""

    __slots__ = ("_render_fn", "_source")

    _render_fn: Callable[[dict[str, object], list[str]], None]
    _source: str

    def __init__(self, render_fn: Callable[[dict[str, object], list[str]], None], source: str, /):
        self._render_fn = render_fn
        self._source = source

    def render(self, *, args: dict[str, object] | None = None) -> str:
        resolved = args or {}
        _render_vars.set(resolved)
        parts: list[str] = []
        self._render_fn(resolved, parts)
        return "".join(parts)

    def stream(self, *, args: dict[str, object] | None = None) -> Generator[str]:
        yield self.render(args=args)

    async def astream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]:
        yield self.render(args=args)

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"CompiledTemplate(<{len(self._source)} chars source>)"


def compile(node: ContentNode | Fragment) -> CompiledTemplate:
    """Compile a node or fragment into a CompiledTemplate."""
    if isinstance(node, Fragment):
        root = node.root
        if not isinstance(root, ContentNode):
            raise TypeError("Cannot compile a Fragment whose root is not a ContentNode")
        node = root
    render_fn, source = compile_to_function(node)
    return CompiledTemplate(render_fn, source)
