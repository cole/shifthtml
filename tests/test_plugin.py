from collections.abc import Generator

import pytest

from shifthtml import Element, Fragment, div, p, span
from shifthtml.element import ContentNode
from shifthtml.plugin import _registry, register
from shifthtml.stream import defer

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
    result = (div() >> (p() >> "hello")).render()
    assert result == "<div>[<p>hello</p>]</div>"


def test_no_plugins_renders_normally():
    result = (div() >> "hello").render()
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
    result = (div() >> (p() >> "hello")).render()
    assert result == "<div>[FIRST]</div>"


def test_plugin_pass_through():
    class NoopPlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

    register(NoopPlugin())
    result = (div() >> (p() >> "hello", span() >> "world")).render()
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
    result = (div() >> "hello").render()
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
    result = (div() >> (p() >> "hello")).render()
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
    result = (div() >> "hello").render()
    assert result == "<!-- preamble --><div>hello</div>"


async def test_async_custom_plugin():
    register(WrapperPlugin())

    async def get_content():
        return p() >> "async hello"

    result = "".join([chunk async for chunk in (div() >> get_content).astream()])
    assert result == "<div>[<p>async hello</p>]</div>"


async def test_async_pre_render_hook():
    class AsyncPreamblePlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        async def apre_render(self, ctx):
            yield "<!-- async preamble -->"

    register(AsyncPreamblePlugin())
    chunks = [chunk async for chunk in (div() >> "hello").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<!-- async preamble --><div>hello</div>"


async def test_async_post_render_hook():
    class AsyncFooterPlugin:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        async def apost_render(self, ctx):
            yield "<!-- async footer -->"

    register(AsyncFooterPlugin())
    chunks = [chunk async for chunk in (div() >> "hello").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<div>hello<!-- async footer --></div>"


async def test_async_post_render_node_hook():
    class AsyncNodeWatcher:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        async def apost_render_node(self, node, ctx):
            if isinstance(node, Element) and node.tag == "p":
                yield "<!-- after p -->"

    register(AsyncNodeWatcher())
    chunks = [chunk async for chunk in (div() >> (p() >> "hi")).astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<div><p>hi</p><!-- after p --></div>"


async def test_async_pre_render_node_hook():
    class AsyncWrapperPlugin:
        def apre_render_node(self, node, astream, ctx):
            if not isinstance(node, Element) or node.tag != "p":
                return None
            return self._render_wrapped(node, astream)

        async def _render_wrapped(self, node, astream):
            yield "["
            async for chunk in astream(node):
                yield chunk
            yield "]"

        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

    register(AsyncWrapperPlugin())
    chunks = [chunk async for chunk in (div() >> (p() >> "async")).astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<div>[<p>async</p>]</div>"


def test_content_node_root_with_plugin():
    class InterceptAll:
        def pre_render_node(self, node, stream, ctx):
            if isinstance(node, ContentNode) and not isinstance(node, Element):
                return iter(["[ROOT]"])
            return None

        def post_render(self, ctx):
            return
            yield

    register(InterceptAll())
    root = ContentNode()
    root.append_child((p() >> "child").root)
    result = root.render()
    assert result == "[ROOT]"


def test_content_node_root_stream_with_plugin():
    class AddFooter:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            yield "<!-- footer -->"

    register(AddFooter())
    root = ContentNode()
    root.append_child((p() >> "text").root)
    chunks = list(root.stream())
    assert "".join(chunks) == "<p>text</p><!-- footer -->"


async def test_element_root_astream_plugin_intercepts():
    class AsyncInterceptDiv:
        def apre_render_node(self, node, astream, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return self._wrap(node, astream)
            return None

        async def _wrap(self, node, astream):
            yield "[["
            async for chunk in astream(node):
                yield chunk
            yield "]]"

        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

    register(AsyncInterceptDiv())
    chunks = [chunk async for chunk in (div() >> "inner").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "[[<div>inner</div>]]"


async def test_element_root_astream_plugin_with_post_hooks():
    class AsyncInterceptWithHooks:
        def apre_render_node(self, node, astream, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return self._wrap(node, astream)
            return None

        async def _wrap(self, node, astream):
            yield "[["
            async for chunk in astream(node):
                yield chunk
            yield "]]"

        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            yield "<!-- post -->"

        async def apost_render_node(self, node, ctx):
            if isinstance(node, Element) and node.tag == "div":
                yield "<!-- after div -->"

    register(AsyncInterceptWithHooks())
    chunks = [chunk async for chunk in (div() >> "inner").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert "[[" in result
    assert "<!-- after div -->" in result


async def test_element_root_astream_sync_plugin_fallback():
    class SyncInterceptWithHooks:
        def pre_render_node(self, node, stream, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return iter(["<replaced />"])
            return None

        def post_render(self, ctx):
            yield "<!-- sync post -->"

        def post_render_node(self, node, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return iter(["<!-- after -->"])
            return None

    register(SyncInterceptWithHooks())
    chunks = [chunk async for chunk in (div() >> "inner").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<replaced /><!-- after --><!-- sync post -->"


async def test_content_node_root_astream_with_plugin():
    class AsyncAddFooter:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        async def apost_render(self, ctx):
            yield "<!-- async footer -->"

    register(AsyncAddFooter())
    root = ContentNode()
    root.append_child((p() >> "text").root)
    chunks = [chunk async for chunk in root.astream(min_chunk_size=None)]
    assert "".join(chunks) == "<p>text</p><!-- async footer -->"


async def test_element_root_astream_no_intercept_post_render_node():
    class PostRenderNodeOnly:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def post_render_node(self, node, ctx):
            if isinstance(node, Element) and node.tag == "div":
                return iter(["<!-- post node -->"])
            return None

    register(PostRenderNodeOnly())
    chunks = [chunk async for chunk in (div() >> "hi").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<div>hi</div><!-- post node -->"


async def test_async_pre_render_all_sync_fallback():
    class SyncPreambleOnly:
        def pre_render_node(self, node, stream, ctx):
            return None

        def post_render(self, ctx):
            return
            yield

        def pre_render(self, ctx):
            yield "<!-- sync preamble -->"

    register(SyncPreambleOnly())
    chunks = [chunk async for chunk in (div() >> "hi").astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert result == "<!-- sync preamble --><div>hi</div>"


async def test_async_defer():
    async def get_content():
        return span() >> "loaded"

    page = div() >> (
        p() >> "before",
        defer("slot-1", div() >> get_content, loading="Loading..."),
        p() >> "after",
    )
    result = "".join([chunk async for chunk in page.astream()])
    assert result == (
        "<div>"
        "<p>before</p>"
        '<div id="slot-1">Loading...</div>'
        "<p>after</p>"
        '<shift-update action="replace" target="slot-1"><template>'
        "<div><span>loaded</span></div>"
        "</template><shift-done></shift-done></shift-update>"
        "</div>"
    )
