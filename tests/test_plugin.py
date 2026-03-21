from collections.abc import Generator

import pytest

from shifthtml import Fragment, div, p, shift, span
from shifthtml.defer import defer
from shifthtml.element import Deferred, Text
from shifthtml.plugin import _registry, register

pytestmark = pytest.mark.anyio


class UppercaseTextPlugin:
    """Test plugin that uppercases all text nodes."""

    def pre_render_node(self, node, ctx):
        if not isinstance(node, Text):
            return None
        return self._render_upper(node)

    def _render_upper(self, node):
        yield str(node.content).upper()

    def post_render(self, ctx):
        return
        yield


def test_custom_plugin_intercepts_render():
    register(UppercaseTextPlugin())
    result = str(shift(div >> "hello"))
    assert result == "<div>HELLO</div>"


def test_no_plugins_renders_normally():
    result = str(shift(div >> "hello"))
    assert result == "<div>hello</div>"


def test_plugin_ordering_first_match_wins():
    class FirstPlugin:
        def pre_render_node(self, node, ctx):
            if isinstance(node, Text):
                return iter(["FIRST"])
            return None

        def post_render(self, ctx):
            return
            yield

    class SecondPlugin:
        def pre_render_node(self, node, ctx):
            if isinstance(node, Text):
                return iter(["SECOND"])
            return None

        def post_render(self, ctx):
            return
            yield

    register(FirstPlugin())
    register(SecondPlugin())
    result = str(shift(div >> "hello"))
    assert result == "<div>FIRST</div>"


def test_plugin_pass_through():
    """Plugin returning None passes to default rendering."""

    class NoopPlugin:
        def pre_render_node(self, node, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

    register(NoopPlugin())
    result = str(shift(div >> (p >> "hello", span >> "world")))
    assert result == "<div><p>hello</p><span>world</span></div>"


def test_deferred_without_plugin_raises():
    node = Deferred(p(), slot_name="slot-1")
    with pytest.raises(TypeError, match="Deferred nodes require DeferPlugin"):
        "".join(node.render())


def test_defer_auto_registers():
    assert len(_registry) == 0
    defer("slot-1", p >> "content")
    assert len(_registry) == 1


def test_defer_registration_idempotent():
    defer("slot-1", p >> "a")
    defer("slot-2", p >> "b")
    assert len(_registry) == 1


def test_fragment_without_plugins():
    d = div()
    frag = Fragment(d, d)
    frag.append(p())
    result = str(frag)
    assert result == "<div><p></p></div>"


def test_post_render():
    class FooterPlugin:
        def pre_render_node(self, node, ctx):
            return None

        def post_render(self, ctx) -> Generator[str]:
            yield "<!-- footer -->"

    register(FooterPlugin())
    result = str(shift(div >> "hello"))
    assert result == "<div>hello<!-- footer --></div>"


def test_post_render_node():
    class CommentAfterDivPlugin:
        def pre_render_node(self, node, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def post_render_node(self, node, ctx):
            from shifthtml.element import Element

            if isinstance(node, Element) and node.tag == "div":
                return iter(["<!-- after div -->"])
            return None

    register(CommentAfterDivPlugin())
    result = str(shift(div >> (p >> "hello")))
    assert result == "<div><p>hello</p></div><!-- after div -->"


def test_pre_render():
    class PreamblePlugin:
        def pre_render_node(self, node, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def pre_render(self, ctx):
            yield "<!-- preamble -->"

    register(PreamblePlugin())
    result = str(shift(div >> "hello"))
    assert result == "<!-- preamble --><div>hello</div>"


async def test_async_custom_plugin():
    register(UppercaseTextPlugin())

    async def get_text():
        return "async hello"

    page = shift(div >> get_text)
    result = "".join([chunk async for chunk in page.arender()])
    assert result == "<div>ASYNC HELLO</div>"


async def test_async_defer():
    async def get_content():
        return span >> "loaded"

    page = shift(
        div
        >> (
            p >> "before",
            defer("slot-1", div >> get_content, loading="Loading..."),
            p >> "after",
        )
    )
    result = "".join([chunk async for chunk in page.arender()])
    assert result == (
        "<div>"
        "<p>before</p>"
        '<div id="p:slot-1">Loading...</div>'
        "<p>after</p>"
        '<script>document.getElementById("p:slot-1").outerHTML=`<div><span>loaded<\\/span><\\/div>`</script>'
        "</div>"
    )
