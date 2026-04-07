from shifthtml import div, li, span
from shifthtml.element import ContentNode
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


def test_sse_with_live_mutation_fragment():
    result = sse(replace("x", div(id="x") >> "new").fragment())
    assert result == (
        'data: <shift-update action="replace" target="x">'
        '<template><div id="x">new</div></template>'
        "<shift-done></shift-done></shift-update>\n\n"
    )


def test_sse_with_multiple_mutation_fragments():
    wrapper = ContentNode()
    wrapper.append_child(replace("a", span() >> "1").fragment().root)
    wrapper.append_child(replace("b", li() >> "2").fragment().root)
    result = sse(wrapper)
    assert result == (
        "data: "
        '<shift-update action="replace" target="a">'
        "<template><span>1</span></template>"
        "<shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="b">'
        "<template><li>2</li></template>"
        "<shift-done></shift-done></shift-update>"
        "\n\n"
    )
