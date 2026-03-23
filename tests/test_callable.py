from shifthtml import (
    Lazy,
    div,
    img,
    p,
    shift,
)


def test_render_single_node_callable():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div >> user_avatar,
    )

    assert str(tag) == '<div><img id="photo" src="https://example.com/photo.jpg" /></div>'


def test_render_callable_in_nodelist():
    def nested_text():
        return p >> "some text"

    tag = shift(
        div
        >> (
            nested_text,
            p >> "other text",
        )
    )

    assert str(tag) == "<div><p>some text</p><p>other text</p></div>"


def test_render_callable_last_in_sequence():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div
        >> (
            p >> "text",
            user_avatar,
        )
    )

    assert str(tag) == '<div><p>text</p><img id="photo" src="https://example.com/photo.jpg" /></div>'


def test_render_single_callable_nested_return():
    def photo_component():
        return div({"id": "div2"}) >> img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div >> photo_component,
    )

    assert str(tag) == '<div><div id="div2"><img id="photo" src="https://example.com/photo.jpg" /></div></div>'


def test_lazy_node_renders_callable_result():
    node = Lazy(lambda: p >> "lazy content")
    assert "".join(node.render()) == "<p>lazy content</p>"


def test_lazy_node_none_renders_empty():
    node = Lazy(lambda: None)
    assert "".join(node.render()) == ""


def test_callable_returning_tuple():
    def multi():
        return (p >> "one", p >> "two")

    tag = shift(div >> multi)
    assert str(tag) == "<div><p>one</p><p>two</p></div>"


def test_callable_returning_list():
    def multi():
        return [p >> "a", p >> "b", p >> "c"]

    tag = shift(div >> multi)
    assert str(tag) == "<div><p>a</p><p>b</p><p>c</p></div>"


def test_callable_returning_nested_tuple():
    def multi():
        return (p >> "x", (p >> "y", p >> "z"))

    tag = shift(div >> multi)
    assert str(tag) == "<div><p>x</p><p>y</p><p>z</p></div>"


def test_callable_returning_tuple_with_strings():
    def multi():
        return ("hello ", "world")

    tag = shift(div >> multi)
    assert str(tag) == "<div>hello world</div>"


def test_callable_returning_empty_tuple():
    def multi():
        return ()

    tag = shift(div >> multi)
    assert str(tag) == "<div></div>"
