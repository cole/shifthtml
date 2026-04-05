from shifthtml import (
    Lazy,
    div,
    img,
    p,
)


def test_render_single_node_callable():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> user_avatar
    assert str(tag) == '<div><img id="photo" src="https://example.com/photo.jpg" /></div>'


def test_render_callable_in_nodelist():
    def nested_text():
        return p() >> "some text"

    tag = div() >> (nested_text, p() >> "other text")
    assert str(tag) == "<div><p>some text</p><p>other text</p></div>"


def test_render_callable_last_in_sequence():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> (p() >> "text", user_avatar)
    assert str(tag) == '<div><p>text</p><img id="photo" src="https://example.com/photo.jpg" /></div>'


def test_render_single_callable_nested_return():
    def photo_component():
        return div({"id": "div2"}) >> img(id="photo", src="https://example.com/photo.jpg")

    tag = div() >> photo_component
    assert str(tag) == '<div><div id="div2"><img id="photo" src="https://example.com/photo.jpg" /></div></div>'


def test_lazy_node_renders():
    node = Lazy(lambda: p() >> "lazy content")
    assert node.render() == "<p>lazy content</p>"


def test_lazy_node_none_renders_empty():
    node = Lazy(lambda: None)
    assert node.render() == ""


def test_callable_returning_tuple():
    def multi():
        return (p() >> "one", p() >> "two")

    tag = div() >> multi
    assert str(tag) == "<div><p>one</p><p>two</p></div>"


def test_callable_returning_list():
    def multi():
        return [p() >> "a", p() >> "b", p() >> "c"]

    tag = div() >> multi
    assert str(tag) == "<div><p>a</p><p>b</p><p>c</p></div>"


def test_callable_returning_nested_tuple():
    def multi():
        return (p() >> "x", (p() >> "y", p() >> "z"))

    tag = div() >> multi
    assert str(tag) == "<div><p>x</p><p>y</p><p>z</p></div>"


def test_callable_returning_tuple_with_strings():
    def multi():
        return ("hello ", "world")

    tag = div() >> multi
    assert str(tag) == "<div>hello world</div>"


def test_callable_returning_empty_tuple():
    def multi():
        return ()

    tag = div() >> multi
    assert str(tag) == "<div></div>"


def test_lazy_with_positional_args():
    def card(title, subtitle):
        return div() >> (p() >> title, p() >> subtitle)

    node = div() >> Lazy(card, "Hello", "World")
    assert str(node) == "<div><div><p>Hello</p><p>World</p></div></div>"


def test_lazy_with_keyword_args():
    def card(title="default"):
        return p() >> title

    node = div() >> Lazy(card, title="Custom")
    assert str(node) == "<div><p>Custom</p></div>"


def test_lazy_with_mixed_args():
    def card(title, body="default"):
        return div() >> (p() >> title, p() >> body)

    node = div() >> Lazy(card, "Hello", body="World")
    assert str(node) == "<div><div><p>Hello</p><p>World</p></div></div>"


def test_lazy_args_repr():
    def my_fn():
        pass

    node = Lazy(my_fn, "a", key="val")
    assert "Lazy(" in repr(node)
    assert "'a'" in repr(node)
    assert "key='val'" in repr(node)


def test_lazy_no_args_unchanged():
    node = Lazy(lambda: p() >> "text")
    assert node.render() == "<p>text</p>"
