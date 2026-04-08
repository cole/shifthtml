from shifthtml import Lazy, Var, div, h1, li, p, ul


def test_render_cache_populated_on_first_render():
    frag = div() >> (p() >> "hello", p() >> "world")
    assert frag._render_cache is None
    frag.render()
    assert frag._render_cache is not None


def test_render_cache_reused_on_second_render():
    frag = div() >> (p() >> "hello", p() >> "world")
    frag.render()
    cache = frag._render_cache
    frag.render()
    assert frag._render_cache is cache


def test_render_cache_invalidated_by_rshift_string():
    frag = div() >> "hello"
    frag.render()
    assert frag._render_cache is not None
    frag >> " world"
    assert frag._render_cache is None
    assert frag.render() == "<div>hello world</div>"


def test_render_cache_invalidated_by_rshift_node():
    frag = div() >> "hello"
    frag.render()
    assert frag._render_cache is not None
    frag >> (p() >> "added")
    assert frag._render_cache is None
    assert frag.render() == "<div>hello<p>added</p></div>"


def test_render_cache_invalidated_by_rshift_tuple():
    frag = div() >> "first"
    frag.render()
    frag >> ("second", "third")
    assert frag._render_cache is None
    assert frag.render() == "<div>firstsecondthird</div>"


def test_render_cache_invalidated_by_append():
    frag = div() >> "hello"
    frag.render()
    assert frag._render_cache is not None
    frag.append(p() >> "appended")
    assert frag._render_cache is None
    assert frag.render() == "<div>hello<p>appended</p></div>"


def test_render_cache_not_set_for_none_rshift():
    frag = div() >> "hello"
    frag.render()
    cache = frag._render_cache
    result = frag >> None
    assert result is None
    # Original fragment cache untouched since >> None short-circuits
    assert frag._render_cache is cache


def test_render_cache_with_vars():
    title = Var("title")
    frag = div() >> t"Title: {title}"
    assert frag.render(args={"title": "A"}) == "<div>Title: A</div>"
    assert frag._render_cache is not None
    assert frag.render(args={"title": "B"}) == "<div>Title: B</div>"


def test_render_cache_rebuilt_after_invalidation():
    frag = div() >> "original"
    frag.render()
    first_cache = frag._render_cache
    frag >> " extra"
    frag.render()
    second_cache = frag._render_cache
    assert second_cache is not None
    assert second_cache is not first_cache
