from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, NoReturn

from .rendering import RenderContext, _collect_result, arender_result
from .tree import Node, _render_vars
from .types import _MISSING, NodeContent


class ConditionalNode(Node):
    """Renders content conditionally based on a Var's truthiness."""

    __slots__ = ("var", "if_true", "if_false")

    var: Var
    if_true: NodeContent
    if_false: NodeContent | None

    def __init__(self, var: Var, if_true: NodeContent, if_false: NodeContent | None = None):
        self.parent_node = None
        self.children = []
        self.var = var
        self.if_true = if_true
        self.if_false = if_false

    def __repr__(self) -> str:
        if self.if_false is not None:
            return f"ConditionalNode({self.var!r}, {self.if_true!r}, {self.if_false!r})"
        return f"ConditionalNode({self.var!r}, {self.if_true!r})"

    def __replace__(self, **changes: object) -> ConditionalNode:
        return ConditionalNode(self.var, self.if_true, self.if_false)

    def __or__(self, content: NodeContent, /) -> ConditionalNode:
        if self.if_false is not None:
            raise TypeError("ConditionalNode already has an else branch")
        return ConditionalNode(self.var, self.if_true, if_false=content)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support >> \u2014 content is set via & and |")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support children")

    def _collect(self, buf: list[str]) -> None:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        _collect_result(branch, buf)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        buf: list[str] = []
        self._collect(buf)
        if buf:
            yield "".join(buf)

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        async for chunk in arender_result(branch, ctx):
            yield chunk


class IterationNode(Node):
    """Renders content for each item in a Var's iterable value."""

    __slots__ = ("var", "body_fn")

    var: Var
    body_fn: Callable[[Any], NodeContent]

    def __init__(self, var: Var, body_fn: Callable[[Any], NodeContent]):
        self.parent_node = None
        self.children = []
        self.var = var
        self.body_fn = body_fn

    def __repr__(self) -> str:
        return f"IterationNode({self.var!r}, {self.body_fn!r})"

    def __replace__(self, **changes: object) -> IterationNode:
        return IterationNode(self.var, self.body_fn)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("IterationNode does not support >> \u2014 content is set via .map()")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("IterationNode does not support children")

    def _collect(self, buf: list[str]) -> None:
        items = self.var()
        for item in items:
            _collect_result(self.body_fn(item), buf)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        buf: list[str] = []
        self._collect(buf)
        if buf:
            yield "".join(buf)

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        items = self.var()
        for item in items:
            async for chunk in arender_result(self.body_fn(item), ctx):
                yield chunk


class Var:
    """A named variable for use in preserved trees.

    Callable \u2014 works in t-string interpolations (evaluated at render time)
    and auto-wraps as Lazy when used as a child node via >>.

    Values are passed via render()/stream()/astream() ``args`` parameter.
    """

    __slots__ = ("name", "default")

    def __init__(self, name: str, *, default: object = _MISSING):
        self.name = name
        self.default = default

    def __call__(self) -> Any:
        vars = _render_vars.get()
        if vars and self.name in vars:
            return vars[self.name]
        if self.default is not _MISSING:
            return self.default
        raise LookupError(f"Var {self.name!r} not set")

    def __repr__(self) -> str:
        return f"Var({self.name!r})"

    def __and__(self, content: NodeContent, /) -> ConditionalNode:
        return ConditionalNode(self, content)

    def map(self, fn: Callable[[Any], NodeContent], /) -> IterationNode:
        return IterationNode(self, fn)


class _VarNamespace:
    """Attribute-access shorthand for creating Var instances: ``args.title`` -> ``Var("title")``."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Var:
        return Var(name)

    def __repr__(self) -> str:
        return "args"


args = _VarNamespace()
