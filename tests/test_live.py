from shifthtml import div, li, span, ul
from shifthtml.live import (
    _RUNTIME_JS,
    _SSE_JS,
    after,
    append,
    before,
    prepend,
    remove,
    replace,
    runtime,
)


def test_replace_renders_shift_update_element():
    result = replace("counter", div(id="counter") >> "42").render()
    assert result == (
        '<shift-update action="replace" target="counter"><template><div id="counter">42</div></template></shift-update>'
    )


def test_append_renders_shift_update_element():
    result = append("messages", li() >> "Hello").render()
    assert result == (
        '<shift-update action="append" target="messages"><template><li>Hello</li></template></shift-update>'
    )


def test_prepend_renders_shift_update_element():
    result = prepend("list", li() >> "First").render()
    assert result == ('<shift-update action="prepend" target="list"><template><li>First</li></template></shift-update>')


def test_before_renders_shift_update_element():
    result = before("item", span() >> "Before").render()
    assert result == (
        '<shift-update action="before" target="item"><template><span>Before</span></template></shift-update>'
    )


def test_after_renders_shift_update_element():
    result = after("item", span() >> "After").render()
    assert result == (
        '<shift-update action="after" target="item"><template><span>After</span></template></shift-update>'
    )


def test_remove_renders_without_template():
    result = remove("old-banner").render()
    assert result == '<shift-update action="remove" target="old-banner"></shift-update>'


def test_mutation_commands_compose_in_tree():
    result = (
        div()
        >> (
            replace("a", span() >> "new-a"),
            append("b", li() >> "item"),
        )
    ).render()
    assert result == (
        "<div>"
        '<shift-update action="replace" target="a"><template><span>new-a</span></template></shift-update>'
        '<shift-update action="append" target="b"><template><li>item</li></template></shift-update>'
        "</div>"
    )


def test_runtime_renders_script_tag():
    result = runtime().render()
    assert result == f"<script>{_RUNTIME_JS}</script>"


def test_runtime_with_stream_includes_sse_listener():
    result = runtime(stream="/events").render()
    assert result == f"<script>{_RUNTIME_JS}{_SSE_JS}</script>"


def test_replace_with_multiple_children():
    result = replace("box", span() >> "a", span() >> "b").render()
    assert result == (
        '<shift-update action="replace" target="box"><template><span>a</span><span>b</span></template></shift-update>'
    )


def test_mutation_with_nested_tree():
    result = replace("nav", ul(id="nav") >> (li() >> "Home", li() >> "About")).render()
    assert result == (
        '<shift-update action="replace" target="nav">'
        '<template><ul id="nav"><li>Home</li><li>About</li></ul></template>'
        "</shift-update>"
    )
