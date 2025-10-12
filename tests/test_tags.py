from shifthtml import (
    body,
    div,
    html,
)


def test_render_html_includes_doctype():
    tag = html >> (body >> (div >> "stuff"))
    assert str(tag) == "<!DOCTYPE html><html><body><div>stuff</div></body></html>"
