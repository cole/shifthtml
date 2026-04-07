from __future__ import annotations

from .element import Fragment
from .tags import script

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

# Legacy alias
_RUNTIME_JS = _APPLY_JS + _CUSTOM_ELEMENT_JS


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


__all__ = ("runtime",)
