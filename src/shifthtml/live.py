from __future__ import annotations

from typing import ClassVar

from .element import Element, Fragment
from .tags import script, template
from .types import NodeContent


class ShiftUpdateElement(Element):
    tag: ClassVar[str] = "shift-update"


class ShiftDoneElement(Element):
    tag: ClassVar[str] = "shift-done"


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


def replace(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="replace", target=target) >> (template() >> content, _MARKER)


def append(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="append", target=target) >> (template() >> content, _MARKER)


def prepend(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="prepend", target=target) >> (template() >> content, _MARKER)


def before(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="before", target=target) >> (template() >> content, _MARKER)


def after(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="after", target=target) >> (template() >> content, _MARKER)


def remove(target: str) -> Fragment:
    return ShiftUpdateElement(action="remove", target=target) >> ""


def runtime(stream: str | None = None) -> Fragment:
    """Return a <script> tag that registers the <shift-update> custom element.

    If `stream` is provided, also includes an SSE listener that connects to
    that URL and injects incoming HTML into the document.
    """
    js = _RUNTIME_JS
    if stream is not None:
        js += _SSE_JS
    return script() >> js


__all__ = ("replace", "append", "prepend", "before", "after", "remove", "runtime")
