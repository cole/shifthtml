import time

import anyio
import pytest

from shifthtml import arender, div, p, span
from shifthtml.defer import defer

pytestmark = pytest.mark.anyio


async def test_early_siblings_flush_before_slow_siblings():
    flush_times: list[tuple[str, float]] = []
    start = time.monotonic()

    async def slow():
        await anyio.sleep(0.2)
        return span() >> "slow"

    page = div() >> (p() >> "fast", slow)

    async for chunk in arender(page, min_chunk_size=None):
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
    async for chunk in arender(page):
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
    async for chunk in arender(page, min_chunk_size=None, cancel_scope=scope):
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
    async for chunk in arender(page):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0] == "<div><p>hello</p><p>world</p></div>"


async def test_batching_splits_at_threshold():
    page = div() >> [p() >> f"paragraph-{i}" for i in range(50)]

    chunks: list[str] = []
    async for chunk in arender(page, min_chunk_size=64):
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
    async for chunk in arender(page, min_chunk_size=None):
        chunks.append(chunk)

    assert len(chunks) > 2
    assert "".join(chunks) == "<div><p>a</p><p>b</p></div>"
