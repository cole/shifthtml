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


# Core apply() function — shared by all layers
_APPLY_JS = (
    "function apply(o){"
    "if(Array.isArray(o)){o.forEach(apply);return}"
    "var e=document.getElementById(o.target);"
    "if(!e)return;"
    "if(o.action==='remove')return e.remove();"
    "if(o.action==='replace')return e.outerHTML=o.html;"
    "if(o.action==='append')e.insertAdjacentHTML('beforeend',o.html);"
    "if(o.action==='prepend')e.insertAdjacentHTML('afterbegin',o.html);"
    "if(o.action==='before')e.insertAdjacentHTML('beforebegin',o.html);"
    "if(o.action==='after')e.insertAdjacentHTML('afterend',o.html);"
    "}"
)

# <shift-update> custom element — delegates to apply() for page streaming
_CUSTOM_ELEMENT_JS = (
    "class ShiftUpdate extends HTMLElement{"
    "connectedCallback(){"
    "if(this.getAttribute('action')==='remove'){"
    "apply({action:'remove',target:this.getAttribute('target')});"
    "this.remove();return}"
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
    "var t=this.getAttribute('target');"
    "var a=this.getAttribute('action');"
    "var c=tpl.content.cloneNode(true);"
    "var d=document.createElement('div');"
    "d.append(c);apply({action:a,target:t,html:d.innerHTML});"
    "this.remove()"
    "}}"
    "customElements.define('shift-update',ShiftUpdate);"
)

# SSE connector — parses JSON events and applies mutations
_SSE_JS = "function connectSSE(u){var e=new EventSource(u);e.onmessage=function(m){apply(JSON.parse(m.data))};return e}"

# WebSocket connector — parses JSON messages, auto-reconnects
_WS_JS = (
    "function connectWS(u){"
    "var w=new WebSocket(u);"
    "w.onmessage=function(m){apply(JSON.parse(m.data))};"
    "w.onclose=function(){setTimeout(function(){connectWS(u)},1000)};"
    "return w}"
)

# Legacy aliases for backward compatibility in tests
_RUNTIME_JS = _APPLY_JS + _CUSTOM_ELEMENT_JS


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


def runtime(
    *,
    stream: str | None = None,
    socket: str | None = None,
) -> Fragment:
    """Return a <script> tag with the shift runtime.

    Always includes the core apply() and <shift-update> custom element.
    Optionally adds SSE and/or WebSocket listeners.
    """
    js = _APPLY_JS + _CUSTOM_ELEMENT_JS
    if stream is not None:
        js += _SSE_JS + f'connectSSE("{stream}");'
    if socket is not None:
        js += _WS_JS + f'connectWS("{socket}");'
    return script() >> js


__all__ = ("Mutation", "replace", "append", "prepend", "before", "after", "remove", "runtime")
