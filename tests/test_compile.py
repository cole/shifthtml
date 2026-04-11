import pytest

from shifthtml import (
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
    title,
    ul,
)


def test_compile_static_tree():
    tree = div() >> (h1() >> "Hello", p() >> "World")
    compiled = compile(tree)
    assert compiled.render() == tree.render()


def test_compile_with_vars():
    page = div() >> (h1() >> t"{args.title}", p() >> t"{args.body}")
    compiled = compile(page)

    assert compiled.render(args={"title": "Page 1", "body": "Hello"}) == "<div><h1>Page 1</h1><p>Hello</p></div>"
    assert compiled.render(args={"title": "Page 2", "body": "World"}) == "<div><h1>Page 2</h1><p>World</p></div>"


def test_compile_with_tstrings():
    name = Var("name")
    page = p() >> t"Hello, {name}!"
    compiled = compile(page)

    assert compiled.render(args={"name": "<script>"}) == "<p>Hello, &lt;script&gt;!</p>"


def test_compile_escapes_static_strings():
    tree = div() >> "1 < 2 & 3 > 0"
    compiled = compile(tree)
    assert compiled.render() == "<div>1 &lt; 2 &amp; 3 &gt; 0</div>"


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
    assert compiled.render() == "<div><p>call 1</p></div>"
    assert compiled.render() == "<div><p>call 1</p></div>"
    assert counter[0] == 1


def test_compile_var_as_child():
    page = div() >> args.title
    compiled = compile(page)

    assert compiled.render(args={"title": "Hello"}) == "<div>Hello</div>"
    assert compiled.render(args={"title": "World"}) == "<div>World</div>"


def test_compile_async_raises():
    async def fetch():
        return "data"

    tree = div() >> Lazy(fetch)
    with pytest.raises(TypeError, match="compile\\(\\) cannot eagerly resolve async Lazy nodes"):
        compile(tree)


def test_compile_void_elements():
    tree = div() >> (img(src="cat.jpg"), br())
    compiled = compile(tree)
    assert compiled.render() == '<div><img src="cat.jpg" /><br /></div>'


def test_compile_comment():
    tree = div() >> Comment("a comment")
    compiled = compile(tree)
    assert compiled.render() == "<div><!--a comment--></div>"


def test_compile_nested_templates():
    greeting = Var("greeting")
    name = Var("name")
    page = p() >> t"{greeting}, {name}!"
    compiled = compile(page)

    assert compiled.render(args={"greeting": "Hi", "name": "Alice"}) == "<p>Hi, Alice!</p>"


def test_compile_html_doctype():
    tree = html() >> (head() >> (meta(charset="utf-8"), title() >> "Test"))
    compiled = compile(tree)
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

    assert compile(page).render(args=test_args) == page.render(args=test_args)


def test_compile_var_returning_node():
    page = div() >> args.content
    compiled = compile(page)

    node_result = p() >> "dynamic node"
    assert compiled.render(args={"content": node_result}) == "<div><p>dynamic node</p></div>"


def test_compile_stream():
    page = h1() >> t"{args.title}"
    compiled = compile(page)

    chunks = list(compiled.stream(args={"title": "Streamed"}))
    assert "".join(chunks) == "<h1>Streamed</h1>"


@pytest.mark.anyio
async def test_compile_astream():
    page = h1() >> t"{args.title}"
    compiled = compile(page)

    chunks = [chunk async for chunk in compiled.astream(args={"title": "Async"})]
    assert "".join(chunks) == "<h1>Async</h1>"


def test_compile_empty_fragment():
    tree = div()
    compiled = compile(tree)
    assert compiled.render() == "<div></div>"


def test_compile_fragment_input():
    tree = div() >> (p() >> "a", p() >> "b")
    compiled = compile(tree)
    assert compiled.render() == "<div><p>a</p><p>b</p></div>"


def test_compile_link_void_with_attrs():
    tree = head() >> link(rel="stylesheet", href="/style.css")
    compiled = compile(tree)
    assert compiled.render() == '<head><link rel="stylesheet" href="/style.css" /></head>'


def test_compile_node_var_preserves_args_for_later_vars():
    page = div() >> (args.content, p() >> t"{args.title}")
    compiled = compile(page)

    result = compiled.render(args={"content": p() >> "dynamic", "title": "Hello"})
    assert result == "<div><p>dynamic</p><p>Hello</p></div>"


def test_compile_conditional():
    page = div() >> (args.show & (p() >> "yes"),)
    compiled = compile(page)
    assert compiled.render(args={"show": True}) == "<div><p>yes</p></div>"
    assert compiled.render(args={"show": False}) == "<div></div>"


def test_compile_conditional_with_else():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = compile(page)
    assert compiled.render(args={"show": True}) == "<div><p>yes</p></div>"
    assert compiled.render(args={"show": False}) == "<div><p>no</p></div>"


def test_compile_conditional_callable_branch():
    calls: list[int] = []

    def make_content():
        calls.append(1)
        return p() >> "lazy"

    page = div() >> (args.show & make_content,)
    compiled = compile(page)

    compiled.render(args={"show": False})
    assert calls == []

    compiled.render(args={"show": True})
    assert calls == [1]


def test_compile_conditional_render_parity():
    page = div() >> (h1() >> "Title", args.show & (p() >> "visible"))
    compiled = compile(page)
    for show in (True, False):
        test_args: dict[str, object] = {"show": show}
        assert compiled.render(args=test_args) == page.render(args=test_args)


def test_compile_iteration():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = compile(page)
    assert compiled.render(args={"items": ["a", "b"]}) == "<ul><li>a</li><li>b</li></ul>"
    assert compiled.render(args={"items": []}) == "<ul></ul>"


def test_compile_iteration_render_parity():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = compile(page)
    for items in (["a", "b", "c"], [], ["x"]):
        test_args: dict[str, object] = {"items": items}
        assert compiled.render(args=test_args) == page.render(args=test_args)


@pytest.mark.anyio
async def test_compile_conditional_astream():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = compile(page)
    chunks = [chunk async for chunk in compiled.astream(args={"show": True})]
    assert "".join(chunks) == "<div><p>yes</p></div>"


def test_compile_conditional_stream():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = compile(page)
    chunks = list(compiled.stream(args={"show": False}))
    assert "".join(chunks) == "<div><p>no</p></div>"


def test_compile_conditional_stream_true():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = compile(page)
    chunks = list(compiled.stream(args={"show": True}))
    assert "".join(chunks) == "<div><p>yes</p></div>"


def test_compile_iteration_stream():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = compile(page)
    chunks = list(compiled.stream(args={"items": ["a", "b"]}))
    assert "".join(chunks) == "<ul><li>a</li><li>b</li></ul>"


@pytest.mark.anyio
async def test_compile_conditional_astream_false():
    page = div() >> ((args.show & (p() >> "yes")) | (p() >> "no"),)
    compiled = compile(page)
    chunks = [chunk async for chunk in compiled.astream(args={"show": False})]
    assert "".join(chunks) == "<div><p>no</p></div>"


@pytest.mark.anyio
async def test_compile_iteration_astream():
    page = ul() >> args.items.map(lambda x: li() >> x)
    compiled = compile(page)
    chunks = [chunk async for chunk in compiled.astream(args={"items": ["x", "y"]})]
    assert "".join(chunks) == "<ul><li>x</li><li>y</li></ul>"


def test_compile_conditional_callable_in_branch_compiled():
    page = div() >> (args.show & (lambda: p() >> "lazy"),)
    compiled = compile(page)
    assert compiled.render(args={"show": True}) == "<div><p>lazy</p></div>"
    assert compiled.render(args={"show": False}) == "<div></div>"


def test_compile_conditional_callable_stream():
    page = div() >> (args.show & (lambda: p() >> "lazy"),)
    compiled = compile(page)
    chunks = list(compiled.stream(args={"show": True}))
    assert "".join(chunks) == "<div><p>lazy</p></div>"


@pytest.mark.anyio
async def test_compile_conditional_callable_astream():
    page = div() >> (args.show & (lambda: p() >> "lazy"),)
    compiled = compile(page)
    chunks = [chunk async for chunk in compiled.astream(args={"show": True})]
    assert "".join(chunks) == "<div><p>lazy</p></div>"


def test_compile_conditional_with_list_content():
    page = div() >> (args.show & (p() >> "a", p() >> "b"),)
    compiled = compile(page)
    assert compiled.render(args={"show": True}) == "<div><p>a</p><p>b</p></div>"
