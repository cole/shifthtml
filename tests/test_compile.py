import pytest

from shifthtml import (
    Async,
    Comment,
    Lazy,
    Var,
    args,
    br,
    compile,
    div,
    h1,
    head,
    html,
    img,
    li,
    link,
    meta,
    p,
    render,
    stream,
    title,
    ul,
)


def test_compile_static_tree():
    tree = div() >> (h1() >> "Hello", p() >> "World")
    compiled = compile(tree)
    assert render(compiled) == render(tree)


def test_compile_with_vars():
    page = div() >> (h1() >> t"{args.title}", p() >> t"{args.body}")
    compiled = compile(page)

    assert render(compiled, args={"title": "Page 1", "body": "Hello"}) == "<div><h1>Page 1</h1><p>Hello</p></div>"
    assert render(compiled, args={"title": "Page 2", "body": "World"}) == "<div><h1>Page 2</h1><p>World</p></div>"


def test_compile_with_tstrings():
    name = Var("name")
    page = p() >> t"Hello, {name}!"
    compiled = compile(page)

    assert render(compiled, args={"name": "<script>"}) == "<p>Hello, &lt;script&gt;!</p>"


def test_compile_escapes_static_strings():
    tree = div() >> "1 < 2 & 3 > 0"
    compiled = compile(tree)
    assert render(compiled) == "<div>1 &lt; 2 &amp; 3 &gt; 0</div>"


def test_compile_eager_lazy():
    counter = [0]

    def make_content():
        counter[0] += 1
        return p() >> f"call {counter[0]}"

    tree = div() >> Lazy(make_content)
    compiled = compile(tree)

    # Lazy was called once at compile time
    assert counter[0] == 1
    # Baked result is static — same output every render
    assert render(compiled) == "<div><p>call 1</p></div>"
    assert render(compiled) == "<div><p>call 1</p></div>"
    assert counter[0] == 1


def test_compile_var_as_child():
    page = div() >> args.title
    compiled = compile(page)

    assert render(compiled, args={"title": "Hello"}) == "<div>Hello</div>"
    assert render(compiled, args={"title": "World"}) == "<div>World</div>"


def test_compile_async_raises():
    async def fetch():
        return "data"

    tree = div() >> Async(fetch)
    with pytest.raises(TypeError, match="compile\\(\\) cannot eagerly resolve Async nodes"):
        compile(tree)


def test_compile_void_elements():
    tree = div() >> (img(src="cat.jpg"), br())
    compiled = compile(tree)
    assert render(compiled) == '<div><img src="cat.jpg" /><br /></div>'


def test_compile_comment():
    tree = div() >> Comment("a comment")
    compiled = compile(tree)
    assert render(compiled) == "<div><!--a comment--></div>"


def test_compile_nested_templates():
    greeting = Var("greeting")
    name = Var("name")
    page = p() >> t"{greeting}, {name}!"
    compiled = compile(page)

    assert render(compiled, args={"greeting": "Hi", "name": "Alice"}) == "<p>Hi, Alice!</p>"


def test_compile_html_doctype():
    tree = html() >> (head() >> (meta(charset="utf-8"), title() >> "Test"))
    compiled = compile(tree)
    result = render(compiled)
    assert result.startswith("<!DOCTYPE html><html>")
    assert result == render(tree)


def test_compile_render_parity():
    page = div() >> (
        h1() >> t"{args.title}",
        args.content,
        ul() >> [li() >> t"item {args.idx}"],
    )
    test_args: dict[str, object] = {"title": "Test", "content": "hello", "idx": "1"}

    assert render(compile(page), args=test_args) == render(page, args=test_args)


def test_compile_var_returning_node():
    page = div() >> args.content
    compiled = compile(page)

    node_result = p() >> "dynamic node"
    assert render(compiled, args={"content": node_result}) == "<div><p>dynamic node</p></div>"


def test_compile_stream():
    page = h1() >> t"{args.title}"
    compiled = compile(page)

    chunks = list(stream(compiled, args={"title": "Streamed"}))
    assert "".join(chunks) == "<h1>Streamed</h1>"


@pytest.mark.anyio
async def test_compile_astream():
    from shifthtml import astream

    page = h1() >> t"{args.title}"
    compiled = compile(page)

    chunks = [chunk async for chunk in astream(compiled, args={"title": "Async"})]
    assert "".join(chunks) == "<h1>Async</h1>"


def test_compile_empty_fragment():
    tree = div()
    compiled = compile(tree)
    assert render(compiled) == "<div></div>"


def test_compile_fragment_input():
    tree = div() >> (p() >> "a", p() >> "b")
    compiled = compile(tree)
    assert render(compiled) == "<div><p>a</p><p>b</p></div>"


def test_compile_link_void_with_attrs():
    tree = head() >> link(rel="stylesheet", href="/style.css")
    compiled = compile(tree)
    assert render(compiled) == '<head><link rel="stylesheet" href="/style.css" /></head>'


def test_compile_node_var_preserves_args_for_later_vars():
    page = div() >> (args.content, p() >> t"{args.title}")
    compiled = compile(page)

    result = render(compiled, args={"content": p() >> "dynamic", "title": "Hello"})
    assert result == "<div><p>dynamic</p><p>Hello</p></div>"
