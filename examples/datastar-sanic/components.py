from datastar_py import attribute_generator as data

from shifthtml import body, div, h1, head, html, meta, script, span, style, title

DATASTAR_CDN = "https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js"

CSS = """\
html, body {
  height: 100%;
  width: 100%;
  margin: 0;
}
body {
  font-family: system-ui, -apple-system, sans-serif;
  background: linear-gradient(to right bottom, oklch(0.42 0.05 254), oklch(0.19 0.04 265));
  display: grid;
  place-content: center;
}
h1 {
  color: white;
  margin-bottom: 1.5rem;
}
.time {
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 600;
  background: oklch(0.92 0.03 90);
  color: oklch(0.27 0.01 0 / 0.7);
}
.time .label {
  font-weight: 400;
  opacity: 0.6;
}
"""


def page_head():
    return head >> (
        meta({"charset": "UTF-8"}),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> "ShiftHTML + Datastar + Sanic",
        script(type="module", src=DATASTAR_CDN),
        style >> CSS,
    )


def page(current_time: str):
    return html({"lang": "en"}) >> (
        page_head,
        body(dict(data.signals(currentTime=current_time)))
        >> div(dict(data.init("@get('/updates')")), id="container")
        >> (
            h1 >> "ShiftHTML + Datastar + Sanic",
            time_element(current_time),
            time_signal_display(),
        ),
    )


def time_element(time_str: str):
    return div(id="time-element", classname="time") >> (
        span(classname="label") >> "Element: ",
        time_str,
    )


def time_signal_display():
    return div(classname="time") >> (
        span(classname="label") >> "Signal: ",
        span(dict(data.text("$currentTime"))) >> "...",
    )
