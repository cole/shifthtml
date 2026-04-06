from shifthtml import div, li, span
from shifthtml.live import replace
from shifthtml.stream import sse


def test_sse_formats_simple_node():
    assert sse(div() >> "hi") == "data: <div>hi</div>\n\n"


def test_sse_with_event_name():
    result = sse(div() >> "hi", event="update")
    assert result == "event: update\ndata: <div>hi</div>\n\n"


def test_sse_with_id():
    result = sse(div() >> "hi", id="42")
    assert result == "id: 42\ndata: <div>hi</div>\n\n"


def test_sse_with_event_and_id():
    result = sse(div() >> "hi", event="update", id="42")
    assert result == "event: update\nid: 42\ndata: <div>hi</div>\n\n"


def test_sse_multiline_content():
    result = sse(div() >> (span() >> "a\nb"))
    assert result == "data: <div><span>a\ndata: b</span></div>\n\n"


def test_sse_with_live_mutation():
    result = sse(replace("x", div(id="x") >> "new"))
    assert result == (
        'data: <shift-update action="replace" target="x"><template><div id="x">new</div></template><shift-done></shift-done></shift-update>\n\n'
    )


def test_sse_with_multiple_mutations():
    from shifthtml.element import ContentNode

    wrapper = ContentNode()
    wrapper.append_child(replace("a", span() >> "1").root)
    wrapper.append_child(replace("b", li() >> "2").root)
    result = sse(wrapper)
    assert result == (
        "data: "
        '<shift-update action="replace" target="a"><template><span>1</span></template><shift-done></shift-done></shift-update>'
        '<shift-update action="replace" target="b"><template><li>2</li></template><shift-done></shift-done></shift-update>'
        "\n\n"
    )
