from shifthtml import body, div, h1, html, p


def test_render_h1_template():
    place = "World"
    tag = h1() >> t"Hello, {place}!"
    assert str(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = h1(id=t"{element_id}") >> "Hello, World!"
    assert str(tag) == '<h1 id="testing">Hello, World!</h1>'


def test_render_nesting():
    count = 1
    tag = (
        html()
        >> body({"class": "test", "data-testid": t"body-{count}"})
        >> div()
        >> (h1() >> "Welcome to the Test Page", p() >> "This is a paragraph on the test page.")
    )
    assert str(tag) == (
        '<!DOCTYPE html><html><body class="test" data-testid="body-1">'
        "<div><h1>Welcome to the Test Page</h1>"
        "<p>This is a paragraph on the test page.</p></div></body></html>"
    )
