import pytest

from shifthtml import Lazy, Var, args, div, h1, html, li, p, render, stream, ul


def test_var_in_tstring():
    title = Var("title")
    page = h1() >> t"Hello {title}"

    assert render(page, args={"title": "World"}) == "<h1>Hello World</h1>"
    assert render(page, args={"title": "Alice"}) == "<h1>Hello Alice</h1>"


def test_var_as_child_auto_lazy():
    content = Var("content")
    page = div() >> content

    assert render(page, args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"
    assert render(page, args={"content": ul() >> [li() >> "a", li() >> "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"


def test_var_returns_string():
    name = Var("name")
    page = div() >> name

    assert render(page, args={"name": "plain text"}) == "<div>plain text</div>"


def test_var_in_lazy_lambda():
    items = Var("items")
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in items()])

    assert render(page, args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"
    assert render(page, args={"items": ["x"]}) == "<div><ul><li>x</li></ul></div>"


def test_render_with_args():
    title = Var("title")
    content = Var("content")

    page = html() >> (
        h1() >> t"{title}",
        content,
    )

    result = render(page, args={"title": "Hello", "content": p() >> "world"})
    assert result == "<!DOCTYPE html><html><h1>Hello</h1><p>world</p></html>"


def test_stream_with_args():
    title = Var("title")
    page = h1() >> t"{title}"

    chunks = list(stream(page, args={"title": "Streamed"}))
    assert "".join(chunks) == "<h1>Streamed</h1>"


def test_var_default():
    title = Var("title", default="fallback")
    page = h1() >> t"{title}"

    assert render(page) == "<h1>fallback</h1>"
    assert render(page, args={"title": "override"}) == "<h1>override</h1>"


def test_var_missing_raises():
    title = Var("title")
    page = h1() >> t"{title}"

    with pytest.raises(LookupError, match="Var 'title' not set"):
        render(page)


def test_var_repr():
    assert repr(Var("title")) == "Var('title')"


def test_preserved_tree_multiple_renders():
    title = Var("title")
    count = Var("count")

    page = div() >> (
        h1() >> t"{title}",
        Lazy(lambda: p() >> f"Count: {count()}"),
    )

    assert render(page, args={"title": "First", "count": 1}) == "<div><h1>First</h1><p>Count: 1</p></div>"
    assert render(page, args={"title": "Second", "count": 2}) == "<div><h1>Second</h1><p>Count: 2</p></div>"


def test_shared_var_name():
    a = Var("title")
    b = Var("title")
    page = div() >> (t"{a}", t" and {b}")

    assert render(page, args={"title": "same"}) == "<div>same and same</div>"


def test_args_namespace_tstring():
    page = h1() >> t"Hello {args.title}"

    assert render(page, args={"title": "World"}) == "<h1>Hello World</h1>"


def test_args_namespace_as_child():
    page = div() >> args.content

    assert render(page, args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"


def test_args_namespace_in_lazy():
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in args.items()])

    assert render(page, args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"


def test_args_namespace_repr():
    assert repr(args) == "args"
    assert repr(args.title) == "Var('title')"
