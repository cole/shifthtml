from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from .element import Element, Fragment
from .tags import template
from .tree import Node
from .types import NodeContent

if TYPE_CHECKING:
    from .rendering import RenderContext


class ShiftUpdateElement(Element):
    tag: ClassVar[str] = "shift-update"


class ShiftDoneElement(Element):
    tag: ClassVar[str] = "shift-done"


class _RawText(Node):
    """Yields pre-rendered HTML without escaping."""

    __slots__ = ("_html",)

    def __init__(self, html: str):
        super().__init__()
        self._html = html

    def __replace__(self, /, **changes):
        return _RawText(self._html)

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield self._html

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield self._html


_MARKER = ShiftDoneElement()


def _render(*content: NodeContent) -> str:
    """Render content to an HTML string."""
    return str(Node() >> content)


@dataclass(slots=True)
class Mutation:
    """A DOM mutation that can be delivered over any transport layer."""

    action: str
    target: str
    html: str | None = None

    def json(self) -> str:
        """JSON string for SSE/WebSocket delivery."""
        d: dict[str, str] = {"action": self.action, "target": self.target}
        if self.html is not None:
            d["html"] = self.html
        return json.dumps(d)

    def sse(self, *, event: str | None = None, id: str | None = None) -> str:
        """SSE-formatted event wrapping the JSON payload."""
        parts: list[str] = []
        if event is not None:
            parts.append(f"event: {event}")
        if id is not None:
            parts.append(f"id: {id}")
        parts.append(f"data: {self.json()}")
        parts.append("")
        parts.append("")
        return "\n".join(parts)

    def fragment(self) -> Fragment:
        """<shift-update> fragment for inline page streaming."""
        el = ShiftUpdateElement(action=self.action, target=self.target)
        if self.action == "remove":
            return el >> ""
        html = self.html if self.html is not None else ""
        return el >> (template() >> _RawText(html), _MARKER)


def replace(target: str, *content: NodeContent) -> Mutation:
    return Mutation("replace", target, _render(*content))


def append(target: str, *content: NodeContent) -> Mutation:
    return Mutation("append", target, _render(*content))


def prepend(target: str, *content: NodeContent) -> Mutation:
    return Mutation("prepend", target, _render(*content))


def before(target: str, *content: NodeContent) -> Mutation:
    return Mutation("before", target, _render(*content))


def after(target: str, *content: NodeContent) -> Mutation:
    return Mutation("after", target, _render(*content))


def remove(target: str) -> Mutation:
    return Mutation("remove", target)


def sse(node: Node | Fragment, *, event: str | None = None, id: str | None = None) -> str:
    """Format a renderable node as a Server-Sent Event string."""
    html = str(node)
    parts: list[str] = []
    if event is not None:
        parts.append(f"event: {event}")
    if id is not None:
        parts.append(f"id: {id}")
    for line in html.split("\n"):
        parts.append(f"data: {line}")
    parts.append("")
    parts.append("")
    return "\n".join(parts)


__all__ = ("Mutation", "replace", "append", "prepend", "before", "after", "remove", "sse")
