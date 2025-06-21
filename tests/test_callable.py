from shifthtml import (
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

    assert (
        str(tag)
        == '<div><img id="photo" src="https://example.com/photo.jpg" /></div>'
    )


def test_render_callable_in_sequence():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div
        >> (
            p >> "text",
            user_avatar,
        )
    )

    assert (
        str(tag)
        == '<div><p>text</p><img id="photo" src="https://example.com/photo.jpg" /></div>'
    )


def test_render_single_callable_nested_return():
    def photo_component():
        return div({"id": "div2"}) >> img(
            id="photo", src="https://example.com/photo.jpg"
        )

    tag = shift(
        div >> photo_component,
    )

    assert (
        str(tag)
        == '<div><div id="div2"><img id="photo" src="https://example.com/photo.jpg" /></div></div>'
    )
