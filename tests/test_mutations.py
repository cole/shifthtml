import pytest

from shifthtml import div, li, span, ul
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
from shifthtml.tree import ContainerNode

pytestmark = pytest.mark.anyio

# -- fragment output (page streaming) --


async def test_replace_fragment():
    result = str((await replace("counter", div(id="counter") >> "42")).fragment())
    assert result == (
        '<shift-update action="replace" target="counter">'
        '<template><div id="counter">42</div></template>'
        "<shift-done></shift-done></shift-update>"
    )


async def test_append_fragment():
    result = str((await append("messages", li() >> "Hello")).fragment())
    assert result == (
        '<shift-update action="append" target="messages">'
        "<template><li>Hello</li></template>"
        "<shift-done></shift-done></shift-update>"
    )


async def test_prepend_fragment():
    result = str((await prepend("list", li() >> "First")).fragment())
    assert result == (
        '<shift-update action="prepend" target="list">'
        "<template><li>First</li></template>"
        "<shift-done></shift-done></shift-update>"
    )


async def test_before_fragment():
    result = str((await before("item", span() >> "Before")).fragment())
    assert result == (
        '<shift-update action="before" target="item">'
        "<template><span>Before</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


async def test_after_fragment():
    result = str((await after("item", span() >> "After")).fragment())
    assert result == (
        '<shift-update action="after" target="item">'
        "<template><span>After</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


def test_remove_fragment():
    result = str(remove("old-banner").fragment())
    assert result == '<shift-update action="remove" target="old-banner"></shift-update>'


async def test_fragment_with_multiple_children():
    result = str((await replace("box", span() >> "a", span() >> "b")).fragment())
    assert result == (
        '<shift-update action="replace" target="box">'
        "<template><span>a</span><span>b</span></template>"
        "<shift-done></shift-done></shift-update>"
    )


async def test_fragment_with_nested_tree():
    result = str((await replace("nav", ul(id="nav") >> (li() >> "Home", li() >> "About"))).fragment())
    assert result == (
        '<shift-update action="replace" target="nav">'
        '<template><ul id="nav"><li>Home</li><li>About</li></ul></template>'
        "<shift-done></shift-done></shift-update>"
    )


async def test_fragments_compose_in_tree():
    result = str(
        div()
        >> (
            (await replace("a", span() >> "new-a")).fragment(),
            (await append("b", li() >> "item")).fragment(),
        )
    )
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


async def test_json_replace():
    m = await replace("chat", div(id="chat") >> "hello")
    assert m.json() == '{"action": "replace", "target": "chat", "html": "<div id=\\"chat\\">hello</div>"}'


async def test_json_append():
    m = await append("messages", li() >> "new")
    assert m.json() == '{"action": "append", "target": "messages", "html": "<li>new</li>"}'


def test_json_remove_omits_html():
    m = remove("old")
    assert m.json() == '{"action": "remove", "target": "old"}'


# -- Mutation.sse() --


async def test_mutation_sse_basic():
    m = await replace("x", span() >> "hi")
    assert m.sse() == f"data: {m.json()}\n\n"


async def test_mutation_sse_with_event():
    m = await append("feed", div() >> "item")
    result = m.sse(event="update")
    assert result == f"event: update\ndata: {m.json()}\n\n"


async def test_mutation_sse_with_event_and_id():
    m = await replace("status", span() >> "ok")
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


async def test_sse_formats_simple_node():
    assert await sse(div() >> "hi") == "data: <div>hi</div>\n\n"


async def test_sse_with_event_name():
    result = await sse(div() >> "hi", event="update")
    assert result == "event: update\ndata: <div>hi</div>\n\n"


async def test_sse_with_id():
    result = await sse(div() >> "hi", id="42")
    assert result == "id: 42\ndata: <div>hi</div>\n\n"


async def test_sse_with_event_and_id():
    result = await sse(div() >> "hi", event="update", id="42")
    assert result == "event: update\nid: 42\ndata: <div>hi</div>\n\n"


async def test_sse_multiline_content():
    result = await sse(div() >> (span() >> "a\nb"))
    assert result == "data: <div><span>a\ndata: b</span></div>\n\n"


async def test_sse_with_mutation_fragment():
    result = await sse((await replace("x", div(id="x") >> "new")).fragment())
    assert result == (
        'data: <shift-update action="replace" target="x">'
        '<template><div id="x">new</div></template>'
        "<shift-done></shift-done></shift-update>\n\n"
    )


async def test_sse_with_multiple_mutation_fragments():
    wrapper = ContainerNode()
    wrapper.append_child((await replace("a", span() >> "1")).fragment().root)
    wrapper.append_child((await replace("b", li() >> "2")).fragment().root)
    result = await sse(wrapper)
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
