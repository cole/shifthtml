from shifthtml import (
    html,
    body,
    h1,
    shift
)


def test_render_h1_template():
    place = "World"
    tag = shift(
        h1 >> t"Hello, {place}!"
    )

    assert tag.render() == "<h1>Hello, World!</h1>"


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = shift(
        h1(id=t"{element_id}") >> "Hello, World!"
    )

    assert tag.render() == '<h1 id="testing">Hello, World!</h1>'


def test_render_nesting():
    count = 1
    tag = shift(
        html >> body @ { "class": "test", "data-testid": t"body-{count}" } >> div >> (
            h1 >> "Welcome to the Test Page",
            p >> "This is a paragraph on the test page."
        )
    )

    assert tag.render() == '<html><body class="test" data-testid="body-1"><div><h1>Welcome to the Test Page</h1><p>This is a paragraph on the test page.</p></div></body></html>'
