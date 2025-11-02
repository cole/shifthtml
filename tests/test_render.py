import pytest

from shifthtml import (
    aside,
    body,
    div,
    h1,
    head,
    html,
    img,
    li,
    link,
    main,
    meta,
    p,
    shift,
    style,
    title,
    ul,
)


def test_render_h1_string():
    tag = shift(h1 >> "Hello, World!")

    assert str(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_template():
    place = "World"
    tag = shift(h1 >> f"Hello, {place}!")

    assert str(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_attributes():
    tag = shift(h1({"style": "color: red;"}, id="hello", classname="bighead") >> "Hello, World!")

    assert str(tag) == '<h1 style="color: red;" id="hello" class="bighead">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = shift(h1(id=f"{element_id}") >> "Hello, World!")

    assert str(tag) == '<h1 id="testing">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_name():
    attr_name = "my-test-attr"
    tag = shift(h1(**{attr_name: "foo"}) >> "Hello, World!")

    assert str(tag) == '<h1 my-test-attr="foo">Hello, World!</h1>'


def test_render_h1_attribute_conversion():
    tag = shift(h1(data_testid="foo") >> "Hello, World!")

    assert str(tag) == '<h1 data-testid="foo">Hello, World!</h1>'


def test_render_ul():
    tag = shift(ul >> (li >> "Test", li >> "one", li >> "two"))

    assert str(tag) == "<ul><li>Test</li><li>one</li><li>two</li></ul>"


def test_render_img_attributes_as_keywords():
    tag = shift(img(id="photo", src="https://example.com/photo.jpg"))

    assert str(tag) == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_attributes_with_dict():
    tag = shift(img({"id": "photo", "src": "https://example.com/photo.jpg"}))

    assert str(tag) == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_child_errors():
    with pytest.raises(ValueError):
        shift(img(id="photo", src="https://example.com/photo.jpg") >> "test")


def test_render_nesting():
    count = 1
    tag = shift(
        html()
        >> body({"class": "test", "data-testid": f"body-{count}"})
        >> div()
        >> (h1() >> "Welcome to the Test Page", p() >> "This is a paragraph on the test page.")
    )

    assert (
        str(tag)
        == '<!DOCTYPE html><html><body class="test" data-testid="body-1"><div><h1>Welcome to the Test Page</h1><p>This is a paragraph on the test page.</p></div></body></html>'
    )


def test_render_head_tag():
    tag = shift(
        head()
        >> (
            title() >> "Test Page",
            meta(charset="UTF-8"),
            link(rel="stylesheet", href="style.css"),
            style() >> "body { background-color: #fff; }",
        )
    )

    assert (
        str(tag)
        == '<head><title>Test Page</title><meta charset="UTF-8" /><link rel="stylesheet" href="style.css" /><style>body { background-color: #fff; }</style></head>'
    )


def test_render_multiple_vars():
    tag1 = shift(
        div
        >> (
            p >> "paragraph 1",
            p >> "paragraph 1.5",
        )
    )
    tag2 = shift(div >> p >> "paragraph 2")

    main_tag = shift(
        main
        >> (
            tag1,
            aside >> tag2,
            div(classname="test") >> tag2,
        )
    )

    assert (
        str(main_tag)
        == '<main><div><p>paragraph 1</p><p>paragraph 1.5</p></div><aside><div><p>paragraph 2</p></div></aside><div class="test"><div><p>paragraph 2</p></div></div></main>'
    )


def test_render_h1_classname_list():
    tag = shift(h1(classname=["bighead", "heading", "page1"]) >> "Hello, World!")

    assert str(tag) == '<h1 class="bighead heading page1">Hello, World!</h1>'


def test_render_h1_classname_set():
    tag = shift(h1(classname={"bighead", "heading", "page1"}) >> "Hello, World!")

    assert "bighead" in str(tag)
    assert "heading" in str(tag)
    assert "page1" in str(tag)


def test_render_h1_classname_tuple():
    tag = shift(h1(classname=("bighead", "heading", "page1")) >> "Hello, World!")

    assert str(tag) == '<h1 class="bighead heading page1">Hello, World!</h1>'
