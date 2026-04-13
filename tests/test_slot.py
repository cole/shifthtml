import pytest

from shifthtml import Lazy, Slot, div, h1, html, li, p, slots, ul

pytestmark = pytest.mark.anyio


async def test_slot_in_tstring():
    title = Slot("title")
    page = h1() >> t"Hello {title}"

    assert await page.render(params={"title": "World"}) == "<h1>Hello World</h1>"
    assert await page.render(params={"title": "Alice"}) == "<h1>Hello Alice</h1>"


async def test_slot_as_child_auto_lazy():
    content = Slot("content")
    page = div() >> content

    assert await page.render(params={"content": p() >> "hello"}) == "<div><p>hello</p></div>"
    assert (
        await page.render(params={"content": ul() >> [li() >> "a", li() >> "b"]})
        == "<div><ul><li>a</li><li>b</li></ul></div>"
    )


async def test_slot_returns_string():
    name = Slot("name")
    page = div() >> name

    assert await page.render(params={"name": "plain text"}) == "<div>plain text</div>"


async def test_slot_in_lazy_lambda():
    items = Slot("items")
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in items()])

    assert await page.render(params={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"
    assert await page.render(params={"items": ["x"]}) == "<div><ul><li>x</li></ul></div>"


async def test_render_with_params():
    title = Slot("title")
    content = Slot("content")

    page = html() >> (
        h1() >> t"{title}",
        content,
    )

    result = await page.render(params={"title": "Hello", "content": p() >> "world"})
    assert result == "<!DOCTYPE html><html><h1>Hello</h1><p>world</p></html>"


async def test_stream_with_params():
    title = Slot("title")
    page = h1() >> t"{title}"

    chunks = [chunk async for chunk in page.stream(params={"title": "Streamed"})]
    assert "".join(chunks) == "<h1>Streamed</h1>"


async def test_slot_default():
    title = Slot("title", default="fallback")
    page = h1() >> t"{title}"

    assert await page.render() == "<h1>fallback</h1>"
    assert await page.render(params={"title": "override"}) == "<h1>override</h1>"


async def test_slot_missing_raises():
    title = Slot("title")
    page = h1() >> t"{title}"

    with pytest.raises(LookupError, match="Slot 'title' not filled"):
        await page.render()


def test_slot_repr():
    assert repr(Slot("title")) == "Slot('title')"


async def test_preserved_tree_multiple_renders():
    title = Slot("title")
    count = Slot("count")

    page = div() >> (
        h1() >> t"{title}",
        Lazy(lambda: p() >> f"Count: {count()}"),
    )

    assert await page.render(params={"title": "First", "count": 1}) == "<div><h1>First</h1><p>Count: 1</p></div>"
    assert await page.render(params={"title": "Second", "count": 2}) == "<div><h1>Second</h1><p>Count: 2</p></div>"


async def test_shared_slot_name():
    a = Slot("title")
    b = Slot("title")
    page = div() >> (t"{a}", t" and {b}")

    assert await page.render(params={"title": "same"}) == "<div>same and same</div>"


async def test_slots_namespace_tstring():
    page = h1() >> t"Hello {slots.title}"

    assert await page.render(params={"title": "World"}) == "<h1>Hello World</h1>"


async def test_slots_namespace_as_child():
    page = div() >> slots.content

    assert await page.render(params={"content": p() >> "hello"}) == "<div><p>hello</p></div>"


async def test_slots_namespace_in_lazy():
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in slots.items()])

    assert await page.render(params={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"


def test_slots_namespace_repr():
    assert repr(slots) == "slots"
    assert repr(slots.title) == "Slot('title')"


async def test_slot_default_used_when_missing():
    v = Slot("missing", default="fallback")
    page = h1() >> t"{v}"
    assert await page.render() == "<h1>fallback</h1>"


async def test_slot_default_overridden():
    v = Slot("x", default="fallback")
    page = h1() >> t"{v}"
    assert await page.render(params={"x": "provided"}) == "<h1>provided</h1>"
