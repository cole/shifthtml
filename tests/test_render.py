from shifthtml import shift, h1


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
