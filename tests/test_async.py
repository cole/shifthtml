import time

import anyio
import pytest

from shifthtml import Async, Fragment, div, h1, li, p, shift, span, ul
from shifthtml.defer import defer

pytestmark = pytest.mark.anyio


async def arender(page: Fragment) -> str:
    return "".join([chunk async for chunk in shift(page).arender()])


async def test_async_callable_rendering():
    async def get_content():
        return "hello async"

    page = div >> get_content
    result = await arender(page)
    assert result == "<div>hello async</div>"


async def test_async_callable_returning_node():
    async def get_content():
        return p >> "async paragraph"

    page = div >> get_content
    result = await arender(page)
    assert result == "<div><p>async paragraph</p></div>"


async def test_multiple_async_siblings():
    async def sidebar():
        return ul >> [li >> "item 1", li >> "item 2"]

    async def main_content():
        return p >> "main"

    page = div >> (sidebar, main_content)
    result = await arender(page)
    assert result == "<div><ul><li>item 1</li><li>item 2</li></ul><p>main</p></div>"


async def test_parallel_sibling_rendering():
    """Verify siblings render concurrently by timing."""

    async def slow_a():
        await anyio.sleep(0.1)
        return span >> "A"

    async def slow_b():
        await anyio.sleep(0.1)
        return span >> "B"

    start = time.monotonic()
    page = div >> (slow_a, slow_b)
    result = await arender(page)
    elapsed = time.monotonic() - start

    assert result == "<div><span>A</span><span>B</span></div>"
    assert elapsed < 0.15, f"Expected parallel execution, took {elapsed:.3f}s"


async def test_async_template_interpolation():
    async def get_name():
        return "World"

    page = h1 >> t"Hello, {get_name}"
    result = await arender(page)
    assert result == "<h1>Hello, World</h1>"


async def test_async_template_with_sync_and_async():
    async def get_async():
        return "async"

    def get_sync():
        return "sync"

    page = p >> t"{get_sync} and {get_async}"
    result = await arender(page)
    assert result == "<p>sync and async</p>"


async def test_async_with_deferred():
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
        '<template shadowrootmode="open"><slot name="slot-1">Loading...</slot></template>'
        "<p>after</p>"
        "</div>"
        '<div slot="slot-1"><span>loaded</span></div>'
    )


async def test_async_node_sync_render_raises():
    async def get_content():
        return "hello"

    node = Async(get_content)
    with pytest.raises(TypeError, match="Async nodes require async rendering"):
        "".join(node.render())


async def test_nested_async_callables():
    async def inner():
        return "inner content"

    async def outer():
        return div >> inner

    page = div >> outer
    result = await arender(page)
    assert result == "<div><div>inner content</div></div>"


async def test_mixed_sync_and_async_children():
    async def async_child():
        return span >> "async"

    page = div >> (p >> "sync", async_child, p >> "also sync")
    result = await arender(page)
    assert result == "<div><p>sync</p><span>async</span><p>also sync</p></div>"


async def test_sync_render_unaffected():
    """Sync rendering still works for non-async trees."""
    page = div >> (p >> "hello", span >> "world")
    result = str(shift(page))
    assert result == "<div><p>hello</p><span>world</span></div>"
