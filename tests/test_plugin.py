from collections.abc import Generator

import pytest

from shifthtml import Element, Fragment, div, p, render, span
from shifthtml.defer import defer
from shifthtml.plugin import _registry, register

pytestmark = pytest.mark.anyio


class WrapperPlugin:
    """Test plugin that wraps <p> elements in brackets."""

    def pre_render_node(self, node, stream, ctx):
        if not isinstance(node, Element) or node.tag != "p":
            return None
        return self._render_wrapped(node, stream)

    def _render_wrapped(self, node, stream):
        yield "["
        yield from stream(node)
        yield "]"

    def post_render(self, ctx):
        return
        yield


def test_custom_plugin_intercepts_render():
    register(WrapperPlugin())
    result = render(div() >> (p() >> "hello"))
    assert result == "<div>[<p>hello</p>]</div>"


def test_no_plugins_renders_normally():
    result = render(div() >> "hello")
    assert result == "<div>hello</div>"


def test_plugin_ordering_first_match_wins():
    class FirstPlugin:
        def pre_render_node(self, node, stream, ctx):
            if isinstance(node, Element) and node.tag == "p":
                return iter(["[FIRST]"])
            return None

        def post_render(self, ctx):
            return
            yield

    class SecondPlugin:
        def pre_render_node(self, node, stream, ctx):
            if isinstance(node, Element) and node.tag == "p":
                return iter(["[SECOND]"])
            return None

        def post_render(self, ctx):
            return
            yield

    register(FirstPlugin())
    register(SecondPlugin())
    result = render(div() >> (p() >> "hello"))
    assert result == "<div>[FIRST]</div>"


def test_plugin_pass_through():
    class NoopPlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

    register(NoopPlugin())
    result = render(div() >> (p() >> "hello", span() >> "world"))
    assert result == "<div><p>hello</p><span>world</span></div>"


def test_defer_auto_registers():
    assert len(_registry) == 0
    defer("slot-1", p() >> "content")
    assert len(_registry) == 1


def test_defer_registration_idempotent():
    defer("slot-1", p() >> "a")
    defer("slot-2", p() >> "b")
    assert len(_registry) == 1


def test_fragment_without_plugins():
    d = div()
    frag = Fragment(d, d)
    frag.append(p())
    assert str(frag) == "<div><p></p></div>"


def test_post_render():
    class FooterPlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx) -> Generator[str]:
            yield "<!-- footer -->"

    register(FooterPlugin())
    result = render(div() >> "hello")
    assert result == "<div>hello<!-- footer --></div>"


def test_post_render_node():
    class CommentAfterDivPlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def post_render_node(self, node, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return iter(["<!-- after div -->"])
            return None

    register(CommentAfterDivPlugin())
    result = render(div() >> (p() >> "hello"))
    assert result == "<div><p>hello</p></div><!-- after div -->"


def test_pre_render():
    class PreamblePlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def pre_render(self, ctx):
            yield "<!-- preamble -->"

    register(PreamblePlugin())
    result = render(div() >> "hello")
    assert result == "<!-- preamble --><div>hello</div>"


async def test_async_custom_plugin():
    from shifthtml import astream

    register(WrapperPlugin())

    async def get_content():
        return p() >> "async hello"

    result = "".join([chunk async for chunk in astream(div() >> get_content)])
    assert result == "<div>[<p>async hello</p>]</div>"


async def test_async_defer():
    from shifthtml import astream

    async def get_content():
        return span() >> "loaded"

    page = div() >> (
        p() >> "before",
        defer("slot-1", div() >> get_content, loading="Loading..."),
        p() >> "after",
    )
    result = "".join([chunk async for chunk in astream(page)])
    assert result == (
        "<div>"
        "<p>before</p>"
        '<div id="p:slot-1">Loading...</div>'
        "<p>after</p>"
        '<script>document.getElementById("p:slot-1").outerHTML=`<div><span>loaded<\\/span><\\/div>`</script>'
        "</div>"
    )
