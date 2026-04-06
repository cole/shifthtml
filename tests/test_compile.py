import pytest

from shifthtml import (
    Async,
    Comment,
    Lazy,
    Var,
    args,
    br,
    div,
    h1,
    head,
    html,
    img,
    li,
    link,
    meta,
    p,
    title,
    ul,
)


def test_compile_static_tree():
    tree = div() >> (h1() >> "Hello", p() >> "World")
    compiled = tree.compile()
    assert compiled.render() == tree.render()


def test_compile_with_vars():
    page = div() >> (h1() >> t"{args.title}", p() >> t"{args.body}")
    compiled = page.compile()

    assert compiled.render(args={"title": "Page 1", "body": "Hello"}) == "<div><h1>Page 1</h1><p>Hello</p></div>"
    assert compiled.render(args={"title": "Page 2", "body": "World"}) == "<div><h1>Page 2</h1><p>World</p></div>"


def test_compile_with_tstrings():
    name = Var("name")
    page = p() >> t"Hello, {name}!"
    compiled = page.compile()

    assert compiled.render(args={"name": "<script>"}) == "<p>Hello, &lt;script&gt;!</p>"


def test_compile_escapes_static_strings():
    tree = div() >> "1 < 2 & 3 > 0"
    compiled = tree.compile()
    assert compiled.render() == "<div>1 &lt; 2 &amp; 3 &gt; 0</div>"


def test_compile_eager_lazy():
    counter = [0]

    def make_content():
        counter[0] += 1
        return p() >> f"call {counter[0]}"

    tree = div() >> Lazy(make_content)
    compiled = tree.compile()

    # Lazy was called once at compile time
    assert counter[0] == 1
    # Baked result is static — same output every render
    assert compiled.render() == "<div><p>call 1</p></div>"
    assert compiled.render() == "<div><p>call 1</p></div>"
    assert counter[0] == 1


def test_compile_var_as_child():
    page = div() >> args.title
    compiled = page.compile()

    assert compiled.render(args={"title": "Hello"}) == "<div>Hello</div>"
    assert compiled.render(args={"title": "World"}) == "<div>World</div>"


def test_compile_async_raises():
    async def fetch():
        return "data"

    tree = div() >> Async(fetch)
    with pytest.raises(TypeError, match="compile\\(\\) cannot eagerly resolve Async nodes"):
        tree.compile()


def test_compile_void_elements():
    tree = div() >> (img(src="cat.jpg"), br())
    compiled = tree.compile()
    assert compiled.render() == '<div><img src="cat.jpg" /><br /></div>'


def test_compile_comment():
    tree = div() >> Comment("a comment")
    compiled = tree.compile()
    assert compiled.render() == "<div><!--a comment--></div>"


def test_compile_nested_templates():
    greeting = Var("greeting")
    name = Var("name")
    page = p() >> t"{greeting}, {name}!"
    compiled = page.compile()

    assert compiled.render(args={"greeting": "Hi", "name": "Alice"}) == "<p>Hi, Alice!</p>"


def test_compile_html_doctype():
    tree = html() >> (head() >> (meta(charset="utf-8"), title() >> "Test"))
    compiled = tree.compile()
    result = compiled.render()
    assert result.startswith("<!DOCTYPE html><html>")
    assert result == tree.render()


def test_compile_render_parity():
    page = div() >> (
        h1() >> t"{args.title}",
        args.content,
        ul() >> [li() >> t"item {args.idx}"],
    )
    test_args: dict[str, object] = {"title": "Test", "content": "hello", "idx": "1"}

    assert page.compile().render(args=test_args) == page.render(args=test_args)


def test_compile_var_returning_node():
    page = div() >> args.content
    compiled = page.compile()

    node_result = p() >> "dynamic node"
    assert compiled.render(args={"content": node_result}) == "<div><p>dynamic node</p></div>"


def test_compile_stream():
    page = h1() >> t"{args.title}"
    compiled = page.compile()

    chunks = list(compiled.stream(args={"title": "Streamed"}))
    assert "".join(chunks) == "<h1>Streamed</h1>"


@pytest.mark.anyio
async def test_compile_astream():
    page = h1() >> t"{args.title}"
    compiled = page.compile()

    chunks = [chunk async for chunk in compiled.astream(args={"title": "Async"})]
    assert "".join(chunks) == "<h1>Async</h1>"


def test_compile_empty_fragment():
    tree = div()
    compiled = tree.compile()
    assert compiled.render() == "<div></div>"


def test_compile_fragment_input():
    tree = div() >> (p() >> "a", p() >> "b")
    compiled = tree.compile()
    assert compiled.render() == "<div><p>a</p><p>b</p></div>"


def test_compile_link_void_with_attrs():
    tree = head() >> link(rel="stylesheet", href="/style.css")
    compiled = tree.compile()
    assert compiled.render() == '<head><link rel="stylesheet" href="/style.css" /></head>'


def test_compile_node_var_preserves_args_for_later_vars():
    page = div() >> (args.content, p() >> t"{args.title}")
    compiled = page.compile()

    result = compiled.render(args={"content": p() >> "dynamic", "title": "Hello"})
    assert result == "<div><p>dynamic</p><p>Hello</p></div>"


def test_compile_conditional():
    page = div() >> (args.show & (p() >> "yes"),)
    compiled = page.compile()
    assert compiled.render(args={"show": True}) == "<div><p>yes</p></div>"
    assert compiled.render(args={"show": False}) == "<div></div>"


def test_compile_conditional_with_else():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = page.compile()
    assert compiled.render(args={"show": True}) == "<div><p>yes</p></div>"
    assert compiled.render(args={"show": False}) == "<div><p>no</p></div>"


def test_compile_conditional_callable_branch():
    calls: list[int] = []

    def make_content():
        calls.append(1)
        return p() >> "lazy"

    page = div() >> (args.show & make_content,)
    compiled = page.compile()

    compiled.render(args={"show": False})
    assert calls == []

    compiled.render(args={"show": True})
    assert calls == [1]


def test_compile_conditional_render_parity():
    page = div() >> (h1() >> "Title", args.show & (p() >> "visible"))
    compiled = page.compile()
    for show in (True, False):
        test_args: dict[str, object] = {"show": show}
        assert compiled.render(args=test_args) == page.render(args=test_args)


def test_compile_iteration():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = page.compile()
    assert compiled.render(args={"items": ["a", "b"]}) == "<ul><li>a</li><li>b</li></ul>"
    assert compiled.render(args={"items": []}) == "<ul></ul>"


def test_compile_iteration_render_parity():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = page.compile()
    for items in (["a", "b", "c"], [], ["x"]):
        test_args: dict[str, object] = {"items": items}
        assert compiled.render(args=test_args) == page.render(args=test_args)


@pytest.mark.anyio
async def test_compile_conditional_astream():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = page.compile()
    chunks = [chunk async for chunk in compiled.astream(args={"show": True})]
    assert "".join(chunks) == "<div><p>yes</p></div>"


def test_compile_conditional_stream():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = page.compile()
    chunks = list(compiled.stream(args={"show": False}))
    assert "".join(chunks) == "<div><p>no</p></div>"
