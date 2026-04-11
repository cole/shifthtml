import time

import anyio
import pytest

from shifthtml import div, footer, h1, header, li, main, p, span, ul
from shifthtml.deferred import Deferred, defer

pytestmark = pytest.mark.anyio


# -- defer plugin (sync) --


def test_render_deferred_paragraph():
    tag = div() >> (
        p() >> "Paragraph 1",
        defer("para-2", p() >> "Paragraph 2", loading="Loading..."),
        p() >> "Paragraph 3",
    )
    assert tag.render() == (
        '<div><p>Paragraph 1</p><div id="para-2">Loading...</div><p>Paragraph 3</p>'
        '<shift-update action="replace" target="para-2">'
        "<template><p>Paragraph 2</p></template><shift-done></shift-done></shift-update></div>"
    )


def test_render_deferred_list_and_nested_items():
    tag = div() >> (
        header() >> h1() >> "Deferred streaming",
        main()
        >> defer(
            "list",
            ul() >> (li() >> defer(f"item-{x}", span() >> f"Item {x}", loading="Loading...") for x in range(3)),
            loading="Loading...",
        ),
        footer() >> "Footer content",
    )
    assert tag.render() == (
        "<div><header><h1>Deferred streaming</h1></header>"
        '<main><div id="list">Loading...</div></main>'
        "<footer>Footer content</footer>"
        '<shift-update action="replace" target="list"><template>'
        "<ul>"
        '<li><div id="item-0">Loading...</div></li>'
        '<li><div id="item-1">Loading...</div></li>'
        '<li><div id="item-2">Loading...</div></li>'
        "</ul></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-0">'
        "<template><span>Item 0</span></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-1">'
        "<template><span>Item 1</span></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-2">'
        "<template><span>Item 2</span></template><shift-done></shift-done></shift-update>"
        "</div>"
    )


# -- async streaming --


async def test_early_siblings_flush_before_slow_siblings():
    flush_times: list[tuple[str, float]] = []
    start = time.monotonic()

    async def slow():
        await anyio.sleep(0.2)
        return span() >> "slow"

    page = div() >> (p() >> "fast", slow)

    async for chunk in page.astream(min_chunk_size=None):
        now = time.monotonic() - start
        if "fast" in chunk:
            flush_times.append(("fast", now))
        if "slow" in chunk:
            flush_times.append(("slow", now))

    fast_time = next(t for label, t in flush_times if label == "fast")
    slow_time = next(t for label, t in flush_times if label == "slow")
    assert fast_time < 0.05, f"Fast content should flush immediately, took {fast_time:.3f}s"
    assert slow_time >= 0.15, f"Slow content should wait for async, took {slow_time:.3f}s"


async def test_flush_preserves_document_order():
    async def slow():
        await anyio.sleep(0.1)
        return span() >> "middle"

    page = div() >> (p() >> "first", slow, p() >> "last")
    chunks: list[str] = []
    async for chunk in page.astream():
        chunks.append(chunk)

    result = "".join(chunks)
    assert result == "<div><p>first</p><span>middle</span><p>last</p></div>"


async def test_cancel_scope_stops_deferred_rendering():
    render_count = 0

    async def track_render():
        nonlocal render_count
        render_count += 1
        await anyio.sleep(0.05)
        return span() >> f"result-{render_count}"

    page = div() >> (
        defer("a", div() >> track_render),
        defer("b", div() >> track_render),
    )

    scope = anyio.CancelScope()
    chunks: list[str] = []
    async for chunk in page.astream(min_chunk_size=None, cancel_scope=scope):
        chunks.append(chunk)
        if "result-1" in chunk:
            scope.cancel()

    result = "".join(chunks)
    assert "result-1" in result
    assert "result-2" not in result
    assert render_count == 1


async def test_default_batching_coalesces_small_chunks():
    page = div() >> (p() >> "hello", p() >> "world")

    chunks: list[str] = []
    async for chunk in page.astream():
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0] == "<div><p>hello</p><p>world</p></div>"


async def test_batching_splits_at_threshold():
    page = div() >> [p() >> f"paragraph-{i}" for i in range(50)]

    chunks: list[str] = []
    async for chunk in page.astream(min_chunk_size=64):
        chunks.append(chunk)

    assert len(chunks) > 1
    result = "".join(chunks)
    assert result.startswith("<div>")
    assert result.endswith("</div>")
    assert "paragraph-0" in result
    assert "paragraph-49" in result


async def test_unbuffered_with_zero_min_chunk_size():
    page = div() >> (p() >> "a", p() >> "b")

    chunks: list[str] = []
    async for chunk in page.astream(min_chunk_size=None):
        chunks.append(chunk)

    assert len(chunks) > 2
    assert "".join(chunks) == "<div><p>a</p><p>b</p></div>"


def test_defer_with_node_loading():
    loading = (span() >> "Loading...").root
    tag = div() >> defer("slot", p() >> "Content", loading=loading)
    result = tag.render()
    assert '<div id="slot"><span>Loading...</span></div>' in result
    assert "<p>Content</p>" in result


async def test_async_defer_with_node_loading():
    async def get_content():
        return span() >> "loaded"

    loading = (span() >> "please wait").root
    page = div() >> defer("slot", div() >> get_content, loading=loading)
    chunks = [chunk async for chunk in page.astream(min_chunk_size=None)]
    result = "".join(chunks)
    assert '<div id="slot"><span>please wait</span></div>' in result
    assert "<span>loaded</span>" in result


def test_deferred_replace():
    d = Deferred(p() >> "content", slot_name="slot", loading="wait")
    clone = d.__replace__()
    assert isinstance(clone, Deferred)
    assert clone is not d
    assert clone.slot_name == "slot"
    assert clone.loading == "wait"
