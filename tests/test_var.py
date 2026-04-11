import pytest

from shifthtml import Lazy, Var, args, div, h1, html, li, p, ul

pytestmark = pytest.mark.anyio


async def test_var_in_tstring():
    title = Var("title")
    page = h1() >> t"Hello {title}"

    assert await page.render(args={"title": "World"}) == "<h1>Hello World</h1>"
    assert await page.render(args={"title": "Alice"}) == "<h1>Hello Alice</h1>"


async def test_var_as_child_auto_lazy():
    content = Var("content")
    page = div() >> content

    assert await page.render(args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"
    assert (
        await page.render(args={"content": ul() >> [li() >> "a", li() >> "b"]})
        == "<div><ul><li>a</li><li>b</li></ul></div>"
    )


async def test_var_returns_string():
    name = Var("name")
    page = div() >> name

    assert await page.render(args={"name": "plain text"}) == "<div>plain text</div>"


async def test_var_in_lazy_lambda():
    items = Var("items")
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in items()])

    assert await page.render(args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"
    assert await page.render(args={"items": ["x"]}) == "<div><ul><li>x</li></ul></div>"


async def test_render_with_args():
    title = Var("title")
    content = Var("content")

    page = html() >> (
        h1() >> t"{title}",
        content,
    )

    result = await page.render(args={"title": "Hello", "content": p() >> "world"})
    assert result == "<!DOCTYPE html><html><h1>Hello</h1><p>world</p></html>"


async def test_stream_with_args():
    title = Var("title")
    page = h1() >> t"{title}"

    chunks = [chunk async for chunk in page.stream(args={"title": "Streamed"})]
    assert "".join(chunks) == "<h1>Streamed</h1>"


async def test_var_default():
    title = Var("title", default="fallback")
    page = h1() >> t"{title}"

    assert await page.render() == "<h1>fallback</h1>"
    assert await page.render(args={"title": "override"}) == "<h1>override</h1>"


async def test_var_missing_raises():
    title = Var("title")
    page = h1() >> t"{title}"

    with pytest.raises(LookupError, match="Var 'title' not set"):
        await page.render()


def test_var_repr():
    assert repr(Var("title")) == "Var('title')"


async def test_preserved_tree_multiple_renders():
    title = Var("title")
    count = Var("count")

    page = div() >> (
        h1() >> t"{title}",
        Lazy(lambda: p() >> f"Count: {count()}"),
    )

    assert await page.render(args={"title": "First", "count": 1}) == "<div><h1>First</h1><p>Count: 1</p></div>"
    assert await page.render(args={"title": "Second", "count": 2}) == "<div><h1>Second</h1><p>Count: 2</p></div>"


async def test_shared_var_name():
    a = Var("title")
    b = Var("title")
    page = div() >> (t"{a}", t" and {b}")

    assert await page.render(args={"title": "same"}) == "<div>same and same</div>"


async def test_args_namespace_tstring():
    page = h1() >> t"Hello {args.title}"

    assert await page.render(args={"title": "World"}) == "<h1>Hello World</h1>"


async def test_args_namespace_as_child():
    page = div() >> args.content

    assert await page.render(args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"


async def test_args_namespace_in_lazy():
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in args.items()])

    assert await page.render(args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"


def test_args_namespace_repr():
    assert repr(args) == "args"
    assert repr(args.title) == "Var('title')"


async def test_var_default_used_when_missing():
    v = Var("missing", default="fallback")
    page = h1() >> t"{v}"
    assert await page.render() == "<h1>fallback</h1>"


async def test_var_default_overridden():
    v = Var("x", default="fallback")
    page = h1() >> t"{v}"
    assert await page.render(args={"x": "provided"}) == "<h1>provided</h1>"
