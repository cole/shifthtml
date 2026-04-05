from __future__ import annotations

from .element import Element, Fragment
from .meta import TagMeta
from .tags import script, template
from .types import NodeContent

ShiftUpdateElement = TagMeta("ShiftUpdateElement", (Element,), {"tag": "shift-update"})

_RUNTIME_JS = (
    "class ShiftUpdate extends HTMLElement{"
    "connectedCallback(){"
    "const t=document.getElementById(this.getAttribute('target'));"
    "if(!t)return;"
    "const c=this.querySelector('template')?.content.cloneNode(true);"
    "const a=this.getAttribute('action');"
    "if(a==='replace')t.replaceWith(c);"
    "else if(a==='append')t.append(c);"
    "else if(a==='prepend')t.prepend(c);"
    "else if(a==='before')t.before(c);"
    "else if(a==='after')t.after(c);"
    "else if(a==='remove')t.remove();"
    "this.remove();"
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


def replace(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="replace", target=target) >> (template() >> content)


def append(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="append", target=target) >> (template() >> content)


def prepend(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="prepend", target=target) >> (template() >> content)


def before(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="before", target=target) >> (template() >> content)


def after(target: str, *content: NodeContent) -> Fragment:
    return ShiftUpdateElement(action="after", target=target) >> (template() >> content)


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
