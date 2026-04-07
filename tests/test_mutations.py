from shifthtml import div, li, span, ul
from shifthtml.element import ContentNode
from shifthtml.mutations import (
    Mutation,
    after,
    append,
    before,
    prepend,
    remove,
    replace,
    sse,
)

# -- fragment output (page streaming) --


def test_replace_fragment():
    result = replace("counter", div(id="counter") >> "42").fragment().render()
    assert result == (
        '<shift-update action="replace" target="counter">'
        '<template><div id="counter">42</div></template>'
        "<shift-done></shift-done></shift-update>"
    )


def test_append_fragment():
    result = append("messages", li() >> "Hello").fragment().render()
    assert result == (
        '<shift-update action="append" target="messages">'
        "<template><li>Hello</li></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_prepend_fragment():
    result = prepend("list", li() >> "First").fragment().render()
    assert result == (
        '<shift-update action="prepend" target="list">'
        "<template><li>First</li></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_before_fragment():
    result = before("item", span() >> "Before").fragment().render()
    assert result == (
        '<shift-update action="before" target="item">'
        "<template><span>Before</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_after_fragment():
    result = after("item", span() >> "After").fragment().render()
    assert result == (
        '<shift-update action="after" target="item">'
        "<template><span>After</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_remove_fragment():
    result = remove("old-banner").fragment().render()
    assert result == '<shift-update action="remove" target="old-banner"></shift-update>'


def test_fragment_with_multiple_children():
    result = replace("box", span() >> "a", span() >> "b").fragment().render()
    assert result == (
        '<shift-update action="replace" target="box">'
        "<template><span>a</span><span>b</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_fragment_with_nested_tree():
    result = replace("nav", ul(id="nav") >> (li() >> "Home", li() >> "About")).fragment().render()
    assert result == (
        '<shift-update action="replace" target="nav">'
        '<template><ul id="nav"><li>Home</li><li>About</li></ul></template>'
        "<shift-done></shift-done></shift-update>"
    )


def test_fragments_compose_in_tree():
    result = (
        div()
        >> (
            replace("a", span() >> "new-a").fragment(),
            append("b", li() >> "item").fragment(),
        )
    ).render()
    assert result == (
        "<div>"
        '<shift-update action="replace" target="a">'
        "<template><span>new-a</span></template>"
        "<shift-done></shift-done></shift-update>"
        '<shift-update action="append" target="b">'
        "<template><li>item</li></template>"
        "<shift-done></shift-done></shift-update>"
        "</div>"
    )


# -- JSON output (WebSocket / SSE) --


def test_json_replace():
    m = replace("chat", div(id="chat") >> "hello")
    assert m.json() == '{"action": "replace", "target": "chat", "html": "<div id=\\"chat\\">hello</div>"}'


def test_json_append():
    m = append("messages", li() >> "new")
    assert m.json() == '{"action": "append", "target": "messages", "html": "<li>new</li>"}'


def test_json_remove_omits_html():
    m = remove("old")
    assert m.json() == '{"action": "remove", "target": "old"}'


# -- Mutation.sse() --


def test_mutation_sse_basic():
    m = replace("x", span() >> "hi")
    assert m.sse() == f"data: {m.json()}\n\n"


def test_mutation_sse_with_event():
    m = append("feed", div() >> "item")
    result = m.sse(event="update")
    assert result == f"event: update\ndata: {m.json()}\n\n"


def test_mutation_sse_with_event_and_id():
    m = replace("status", span() >> "ok")
    result = m.sse(event="update", id="42")
    assert result == f"event: update\nid: 42\ndata: {m.json()}\n\n"


# -- Mutation dataclass --


def test_mutation_fields():
    m = Mutation("replace", "target", "<div>hi</div>")
    assert m.action == "replace"
    assert m.target == "target"
    assert m.html == "<div>hi</div>"


def test_mutation_equality():
    a = Mutation("replace", "x", "<p>hi</p>")
    b = Mutation("replace", "x", "<p>hi</p>")
    assert a == b


def test_mutation_html_defaults_to_none():
    m = Mutation("remove", "x")
    assert m.html is None


# -- sse() for renderables --


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


def test_sse_with_mutation_fragment():
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
