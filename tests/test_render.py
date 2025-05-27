import pytest

from shifthtml import shift, h1, ul, li, img


def test_render_h1_string():
    html = (
        h1 >> t"Hello, World!"
    )

    assert shift(html) == "<h1>Hello, World!</h1>"


def test_render_h1_template():
    place = "World"
    html = (
        h1 >> t"Hello, {place}!"
    )

    assert shift(html) == "<h1>Hello, World!</h1>"


def test_render_h1_attributes():
    html = (
        h1(id="bighead") >> t"Hello, World!"
    )

    assert shift(html) == '<h1 id="bighead">Hello, World!</h1>'



def test_render_ul():
    html = (
        ul >> (
            li >> "Test",
            li >> "one",
            li >> "two"
        )
    )

    assert shift(html) == '<ul><li>Test</li><li>one</li><li>two</li></ul>'



def test_render_img_attributes():
    html = (
        img(id="photo", src="https://example.com/photo.jpg")
    )

    assert shift(html) == '<img id="photo" src="https://example.com/photo.jpg" />'



def test_render_img_child_errors():
    with pytest.raises(ValueError):
        html = (
            img(id="photo", src="https://example.com/photo.jpg") >> "test"
        )


