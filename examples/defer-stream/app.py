# /// script
# dependencies = [
#   "flask",
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

from base64 import b64encode

from flask import Flask, Response

from components import page
from shifthtml import shift

app = Flask(__name__)

SLOT_FILLER_JS = b"""\
const hosts = {};
function findHost(name) {
    if (hosts[name]) return hosts[name];
    for (const el of document.querySelectorAll('*')) {
        if (el.shadowRoot) {
            const s = el.shadowRoot.querySelector('slot[name="' + name + '"]');
            if (s) { hosts[name] = el; return el; }
        }
    }
    return null;
}
function fill() {
    for (const el of [...document.body.children]) {
        const s = el.getAttribute('slot');
        if (!s) continue;
        const h = findHost(s);
        if (h && el.parentNode !== h) h.appendChild(el);
    }
}
new MutationObserver(fill).observe(document.body, { childList: true });
fill();
"""

SLOT_FILLER_SRC = f"data:text/javascript;base64,{b64encode(SLOT_FILLER_JS).decode()}"


@app.route("/")
def index():
    return Response(shift(page(SLOT_FILLER_SRC)).render(), content_type="text/html")


if __name__ == "__main__":
    app.run(debug=True)
