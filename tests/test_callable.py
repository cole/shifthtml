from functools import partial

import pytest

from shifthtml import (
    Lazy,
    div,
    img,
    p,
)

pytestmark = pytest.mark.anyio


async def test_render_single_node_callable():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> user_avatar
    assert await tag.render() == '<div><img id="photo" src="https://example.com/photo.jpg" /></div>'


async def test_render_callable_in_nodelist():
    def nested_text():
        return p() >> "some text"

    tag = div() >> (nested_text, p() >> "other text")
    assert await tag.render() == "<div><p>some text</p><p>other text</p></div>"


async def test_render_callable_last_in_sequence():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> (p() >> "text", user_avatar)
    assert await tag.render() == '<div><p>text</p><img id="photo" src="https://example.com/photo.jpg" /></div>'


async def test_render_single_callable_nested_return():
    def photo_component():
        return div({"id": "div2"}) >> img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> photo_component
    assert (
        await tag.render() == '<div><div id="div2"><img id="photo" src="https://example.com/photo.jpg" /></div></div>'
    )


async def test_lazy_node_renders():
    node = Lazy(lambda: p() >> "lazy content")
    assert await node.render() == "<p>lazy content</p>"


async def test_lazy_node_none_renders_empty():
    node = Lazy(lambda: None)
    assert await node.render() == ""


async def test_callable_returning_tuple():
    def multi():
        return (p() >> "one", p() >> "two")

    tag = div() >> multi
    assert await tag.render() == "<div><p>one</p><p>two</p></div>"


async def test_callable_returning_list():
    def multi():
        return [p() >> "a", p() >> "b", p() >> "c"]

    tag = div() >> multi
    assert await tag.render() == "<div><p>a</p><p>b</p><p>c</p></div>"


async def test_callable_returning_nested_tuple():
    def multi():
        return (p() >> "x", (p() >> "y", p() >> "z"))

    tag = div() >> multi
    assert await tag.render() == "<div><p>x</p><p>y</p><p>z</p></div>"


async def test_callable_returning_tuple_with_strings():
    def multi():
        return ("hello ", "world")

    tag = div() >> multi
    assert await tag.render() == "<div>hello world</div>"


async def test_callable_returning_empty_tuple():
    def multi():
        return ()

    tag = div() >> multi
    assert await tag.render() == "<div></div>"


async def test_lazy_with_partial():
    def card(title, subtitle):
        return div() >> (p() >> title, p() >> subtitle)

    node = div() >> Lazy(partial(card, "Hello", "World"))
    assert await node.render() == "<div><div><p>Hello</p><p>World</p></div></div>"


async def test_lazy_with_keyword_partial():
    def card(title="default"):
        return p() >> title

    node = div() >> Lazy(partial(card, title="Custom"))
    assert await node.render() == "<div><p>Custom</p></div>"


async def test_lazy_with_mixed_partial():
    def card(title, body="default"):
        return div() >> (p() >> title, p() >> body)

    node = div() >> Lazy(partial(card, "Hello", body="World"))
    assert await node.render() == "<div><div><p>Hello</p><p>World</p></div></div>"


def test_lazy_repr():
    def my_fn():
        pass

    node = Lazy(my_fn)
    assert "Lazy(" in repr(node)
    assert "my_fn" in repr(node)


async def test_lazy_no_args_unchanged():
    node = Lazy(lambda: p() >> "text")
    assert await node.render() == "<p>text</p>"


def test_lazy_sync_str_raises():
    node = Lazy(lambda: p() >> "text")
    with pytest.raises(TypeError, match="Lazy nodes require async rendering"):
        str(node)
