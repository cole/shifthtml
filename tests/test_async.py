import time

import anyio
import pytest

from shifthtml import Async, div, h1, li, p, span, ul
from shifthtml.defer import defer

pytestmark = pytest.mark.anyio


async def render_str(page) -> str:
    return "".join([chunk async for chunk in page.astream()])


async def test_async_callable_rendering():
    async def get_content():
        return "hello async"

    page = div() >> get_content
    result = await render_str(page)
    assert result == "<div>hello async</div>"


async def test_async_callable_returning_node():
    async def get_content():
        return p() >> "async paragraph"

    page = div() >> get_content
    result = await render_str(page)
    assert result == "<div><p>async paragraph</p></div>"


async def test_multiple_async_siblings():
    async def sidebar():
        return ul() >> [li() >> "item 1", li() >> "item 2"]

    async def main_content():
        return p() >> "main"

    page = div() >> (sidebar, main_content)
    result = await render_str(page)
    assert result == "<div><ul><li>item 1</li><li>item 2</li></ul><p>main</p></div>"


async def test_parallel_sibling_rendering():
    async def slow_a():
        await anyio.sleep(0.1)
        return span() >> "A"

    async def slow_b():
        await anyio.sleep(0.1)
        return span() >> "B"

    start = time.monotonic()
    page = div() >> (slow_a, slow_b)
    result = await render_str(page)
    elapsed = time.monotonic() - start

    assert result == "<div><span>A</span><span>B</span></div>"
    assert elapsed < 0.15, f"Expected parallel execution, took {elapsed:.3f}s"


async def test_async_template_interpolation():
    async def get_name():
        return "World"

    page = h1() >> t"Hello, {get_name}"
    result = await render_str(page)
    assert result == "<h1>Hello, World</h1>"


async def test_async_template_with_sync_and_async():
    async def get_async():
        return "async"

    def get_sync():
        return "sync"

    page = p() >> t"{get_sync} and {get_async}"
    result = await render_str(page)
    assert result == "<p>sync and async</p>"


async def test_async_with_deferred():
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


async def test_async_node_sync_render_raises():
    async def get_content():
        return "hello"

    node = Async(get_content)
    with pytest.raises(TypeError, match="Async nodes require async rendering"):
        node.render()


async def test_nested_async_callables():
    async def inner():
        return "inner content"

    async def outer():
        return div() >> inner

    page = div() >> outer
    result = await render_str(page)
    assert result == "<div><div>inner content</div></div>"


async def test_mixed_sync_and_async_children():
    async def async_child():
        return span() >> "async"

    page = div() >> (p() >> "sync", async_child, p() >> "also sync")
    result = await render_str(page)
    assert result == "<div><p>sync</p><span>async</span><p>also sync</p></div>"


async def test_sync_render_unaffected():
    page = div() >> (p() >> "hello", span() >> "world")
    assert str(page) == "<div><p>hello</p><span>world</span></div>"


async def test_async_callable_returning_tuple():
    async def multi():
        return (p() >> "one", p() >> "two")

    result = await render_str(div() >> multi)
    assert result == "<div><p>one</p><p>two</p></div>"


async def test_async_callable_returning_list():
    async def multi():
        return [span() >> "a", span() >> "b"]

    result = await render_str(div() >> multi)
    assert result == "<div><span>a</span><span>b</span></div>"


async def test_async_with_positional_args():
    async def fetch_greeting(name):
        return p() >> f"Hello, {name}"

    result = await render_str(div() >> Async(fetch_greeting, "World"))
    assert result == "<div><p>Hello, World</p></div>"


async def test_async_with_keyword_args():
    async def fetch_user(user_id=0):
        return span() >> f"user-{user_id}"

    result = await render_str(div() >> Async(fetch_user, user_id=42))
    assert result == "<div><span>user-42</span></div>"
