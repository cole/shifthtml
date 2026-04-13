from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, NoReturn

from .rendering import RenderContext, _collect_result, arender_result
from .tree import Node, _render_params
from .types import _MISSING, NodeContent


class ConditionalNode(Node):
    """Renders content conditionally based on a Slot's truthiness."""

    __slots__ = ("slot", "if_true", "if_false")

    slot: Slot
    if_true: NodeContent
    if_false: NodeContent | None

    def __init__(self, slot: Slot, if_true: NodeContent, if_false: NodeContent | None = None):
        self.parent_node = None
        self.children = []
        self._cursor = None
        self.slot = slot
        self.if_true = if_true
        self.if_false = if_false

    def __repr__(self) -> str:
        if self.if_false is not None:
            return f"ConditionalNode({self.slot!r}, {self.if_true!r}, {self.if_false!r})"
        return f"ConditionalNode({self.slot!r}, {self.if_true!r})"

    def __replace__(self, **changes: object) -> ConditionalNode:
        return ConditionalNode(self.slot, self.if_true, self.if_false)

    def otherwise(self, content: NodeContent, /) -> ConditionalNode:
        if self.if_false is not None:
            raise TypeError("ConditionalNode already has an else branch")
        return ConditionalNode(self.slot, self.if_true, if_false=content)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support >> \u2014 content is set via .then() and .otherwise()")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support children")

    def _collect(self, buf: list[str]) -> None:
        val = self.slot()
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
        val = self.slot()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        async for chunk in arender_result(branch, ctx):
            yield chunk


class IterationNode(Node):
    """Renders content for each item in a Slot's iterable value."""

    __slots__ = ("slot", "body_fn")

    slot: Slot
    body_fn: Callable[[Any], NodeContent]

    def __init__(self, slot: Slot, body_fn: Callable[[Any], NodeContent]):
        self.parent_node = None
        self.children = []
        self._cursor = None
        self.slot = slot
        self.body_fn = body_fn

    def __repr__(self) -> str:
        return f"IterationNode({self.slot!r}, {self.body_fn!r})"

    def __replace__(self, **changes: object) -> IterationNode:
        return IterationNode(self.slot, self.body_fn)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("IterationNode does not support >> \u2014 content is set via .map()")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("IterationNode does not support children")

    def _collect(self, buf: list[str]) -> None:
        items = self.slot()
        for item in items:
            _collect_result(self.body_fn(item), buf)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        buf: list[str] = []
        self._collect(buf)
        if buf:
            yield "".join(buf)

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        items = self.slot()
        for item in items:
            async for chunk in arender_result(self.body_fn(item), ctx):
                yield chunk


class Slot:
    """A named slot in a template, filled by a render-time param.

    Callable \u2014 works in t-string interpolations (evaluated at render time)
    and auto-wraps as Lazy when used as a child node via >>.

    Values are passed via render()/stream()/astream() ``params`` parameter.
    """

    __slots__ = ("name", "default")

    def __init__(self, name: str, *, default: object = _MISSING):
        self.name = name
        self.default = default

    def __call__(self) -> Any:
        params = _render_params.get()
        if params and self.name in params:
            return params[self.name]
        if self.default is not _MISSING:
            return self.default
        raise LookupError(f"Slot {self.name!r} not filled")

    def __repr__(self) -> str:
        return f"Slot({self.name!r})"

    def then(self, content: NodeContent, /) -> ConditionalNode:
        return ConditionalNode(self, content)

    def map(self, fn: Callable[[Any], NodeContent], /) -> IterationNode:
        return IterationNode(self, fn)


class _SlotNamespace:
    """Attribute-access shorthand for creating Slot instances: ``slots.title`` -> ``Slot("title")``."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Slot:
        return Slot(name)

    def __repr__(self) -> str:
        return "slots"


slots = _SlotNamespace()
