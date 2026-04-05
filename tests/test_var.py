import pytest

from shifthtml import Lazy, Var, args, div, h1, html, li, p, ul


def test_var_in_tstring():
    title = Var("title")
    page = h1() >> t"Hello {title}"

    assert page.render(args={"title": "World"}) == "<h1>Hello World</h1>"
    assert page.render(args={"title": "Alice"}) == "<h1>Hello Alice</h1>"


def test_var_as_child_auto_lazy():
    content = Var("content")
    page = div() >> content

    assert page.render(args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"
    assert (
        page.render(args={"content": ul() >> [li() >> "a", li() >> "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"
    )


def test_var_returns_string():
    name = Var("name")
    page = div() >> name

    assert page.render(args={"name": "plain text"}) == "<div>plain text</div>"


def test_var_in_lazy_lambda():
    items = Var("items")
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in items()])

    assert page.render(args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"
    assert page.render(args={"items": ["x"]}) == "<div><ul><li>x</li></ul></div>"


def test_render_with_args():
    title = Var("title")
    content = Var("content")

    page = html() >> (
        h1() >> t"{title}",
        content,
    )

    result = page.render(args={"title": "Hello", "content": p() >> "world"})
    assert result == "<!DOCTYPE html><html><h1>Hello</h1><p>world</p></html>"


def test_stream_with_args():
    title = Var("title")
    page = h1() >> t"{title}"

    chunks = list(page.stream(args={"title": "Streamed"}))
    assert "".join(chunks) == "<h1>Streamed</h1>"


def test_var_default():
    title = Var("title", default="fallback")
    page = h1() >> t"{title}"

    assert page.render() == "<h1>fallback</h1>"
    assert page.render(args={"title": "override"}) == "<h1>override</h1>"


def test_var_missing_raises():
    title = Var("title")
    page = h1() >> t"{title}"

    with pytest.raises(LookupError, match="Var 'title' not set"):
        page.render()


def test_var_repr():
    assert repr(Var("title")) == "Var('title')"


def test_preserved_tree_multiple_renders():
    title = Var("title")
    count = Var("count")

    page = div() >> (
        h1() >> t"{title}",
        Lazy(lambda: p() >> f"Count: {count()}"),
    )

    assert page.render(args={"title": "First", "count": 1}) == "<div><h1>First</h1><p>Count: 1</p></div>"
    assert page.render(args={"title": "Second", "count": 2}) == "<div><h1>Second</h1><p>Count: 2</p></div>"


def test_shared_var_name():
    a = Var("title")
    b = Var("title")
    page = div() >> (t"{a}", t" and {b}")

    assert page.render(args={"title": "same"}) == "<div>same and same</div>"


def test_args_namespace_tstring():
    page = h1() >> t"Hello {args.title}"

    assert page.render(args={"title": "World"}) == "<h1>Hello World</h1>"


def test_args_namespace_as_child():
    page = div() >> args.content

    assert page.render(args={"content": p() >> "hello"}) == "<div><p>hello</p></div>"


def test_args_namespace_in_lazy():
    page = div() >> Lazy(lambda: ul() >> [li() >> x for x in args.items()])

    assert page.render(args={"items": ["a", "b"]}) == "<div><ul><li>a</li><li>b</li></ul></div>"


def test_args_namespace_repr():
    assert repr(args) == "args"
    assert repr(args.title) == "Var('title')"
