from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from .element import ContentNode, Element, Fragment
from .tags import script, template
from .tree import Node
from .types import NodeContent

if TYPE_CHECKING:
    from .plugin import RenderContext


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

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield self._html

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield self._html


_RUNTIME_JS = (
    "class ShiftUpdate extends HTMLElement{"
    "connectedCallback(){"
    "if(this.getAttribute('action')==='remove'){"
    "var t=document.getElementById(this.getAttribute('target'));"
    "if(t)t.remove();this.remove();return}"
    "this._r()||new MutationObserver(function(m,o){"
    "if(this._r())o.disconnect()"
    "}.bind(this)).observe(this,{childList:true})"
    "}"
    "_r(){"
    "if(!this.querySelector('shift-done'))return!1;"
    "var t=this.querySelector('template');"
    "this._apply(t);return!0"
    "}"
    "_apply(tpl){"
    "if(this._d)return;this._d=1;"
    "var t=document.getElementById(this.getAttribute('target'));"
    "if(!t){this.remove();return}"
    "var c=tpl.content.cloneNode(true);"
    "var a=this.getAttribute('action');"
    "if(a==='replace')t.replaceWith(c);"
    "else if(a==='append')t.append(c);"
    "else if(a==='prepend')t.prepend(c);"
    "else if(a==='before')t.before(c);"
    "else if(a==='after')t.after(c);"
    "this.remove()"
    "}}"
    "customElements.define('shift-update',ShiftUpdate);"
)

_SSE_JS = (
    "(function(){var u=document.querySelector('[data-stream]');"
    "if(u){u=u.dataset.stream;"
    "var e=new EventSource(u);"
    "e.onmessage=function(m){document.body.insertAdjacentHTML('beforeend',m.data)};}"
    "})();"
)


_MARKER = ShiftDoneElement()


def _render(*content: NodeContent) -> str:
    """Render content to an HTML string."""
    return (ContentNode() >> content).render()


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


def runtime(stream: str | None = None) -> Fragment:
    """Return a <script> tag that registers the <shift-update> custom element.

    If `stream` is provided, also includes an SSE listener that connects to
    that URL and injects incoming HTML into the document.
    """
    js = _RUNTIME_JS
    if stream is not None:
        js += _SSE_JS
    return script() >> js


__all__ = ("Mutation", "replace", "append", "prepend", "before", "after", "remove", "runtime")
