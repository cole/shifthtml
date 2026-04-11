import pytest

from shifthtml import (
    Comment,
    Fragment,
    Lazy,
    Node,
    Var,
    aside,
    body,
    button,
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
    style,
    title,
    ul,
)
from shifthtml.element import _flatten_into

pytestmark = pytest.mark.anyio


def test_render_h1_string():
    tag = h1() >> "Hello, World!"
    assert str(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_template():
    place = "World"
    tag = h1() >> f"Hello, {place}!"
    assert str(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_attributes():
    tag = h1({"style": "color: red;"}, id="hello", class_="bighead") >> "Hello, World!"
    assert str(tag) == '<h1 style="color: red;" id="hello" class="bighead">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = h1(id=f"{element_id}") >> "Hello, World!"
    assert str(tag) == '<h1 id="testing">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_name():
    attr_name = "my-test-attr"
    tag = h1(**{attr_name: "foo"}) >> "Hello, World!"
    assert str(tag) == '<h1 my-test-attr="foo">Hello, World!</h1>'


def test_render_h1_attribute_conversion():
    tag = h1(data_testid="foo") >> "Hello, World!"
    assert str(tag) == '<h1 data-testid="foo">Hello, World!</h1>'


def test_render_ul():
    tag = ul() >> (li() >> "Test", li() >> "one", li() >> "two")
    assert str(tag) == "<ul><li>Test</li><li>one</li><li>two</li></ul>"


def test_render_img_attributes_as_keywords():
    tag = img(id="photo", src="https://example.com/photo.jpg")
    assert str(tag) == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_attributes_with_dict():
    tag = img({"id": "photo", "src": "https://example.com/photo.jpg"})
    assert str(tag) == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_child_errors():
    with pytest.raises(ValueError):
        img(id="photo", src="https://example.com/photo.jpg") >> "test"


def test_render_nesting():
    count = 1
    tag = (
        html()
        >> body({"class": "test", "data-testid": f"body-{count}"})
        >> div()
        >> (h1() >> "Welcome to the Test Page", p() >> "This is a paragraph on the test page.")
    )
    assert str(tag) == (
        '<!DOCTYPE html><html><body class="test" data-testid="body-1">'
        "<div><h1>Welcome to the Test Page</h1>"
        "<p>This is a paragraph on the test page.</p></div></body></html>"
    )


def test_render_head_tag():
    tag = head() >> (
        title() >> "Test Page",
        meta(charset="UTF-8"),
        link(rel="stylesheet", href="style.css"),
        style() >> "body { background-color: #fff; }",
    )
    assert str(tag) == (
        "<head><title>Test Page</title>"
        '<meta charset="UTF-8" /><link rel="stylesheet" href="style.css" />'
        "<style>body { background-color: #fff; }</style></head>"
    )


def test_render_multiple_vars():
    tag1 = div() >> (p() >> "paragraph 1", p() >> "paragraph 1.5")
    tag2 = div() >> p() >> "paragraph 2"

    main_tag = main() >> (
        tag1,
        aside() >> tag2,
        div(class_="test") >> tag2,
    )
    assert str(main_tag) == (
        "<main><div><p>paragraph 1</p><p>paragraph 1.5</p></div>"
        "<aside><div><p>paragraph 2</p></div></aside>"
        '<div class="test"><div><p>paragraph 2</p></div></div></main>'
    )


def test_render_h1_class_list():
    tag = h1(class_=["bighead", "heading", "page1"]) >> "Hello, World!"
    assert str(tag) == '<h1 class="bighead heading page1">Hello, World!</h1>'


def test_render_h1_class_set():
    tag = h1(class_={"bighead", "heading", "page1"}) >> "Hello, World!"
    assert "bighead" in str(tag)
    assert "heading" in str(tag)
    assert "page1" in str(tag)


def test_render_h1_class_tuple():
    tag = h1(class_=("bighead", "heading", "page1")) >> "Hello, World!"
    assert str(tag) == '<h1 class="bighead heading page1">Hello, World!</h1>'


def test_text_does_not_escape_quotes():
    tag = div() >> 'She said "hello"'
    assert str(tag) == '<div>She said "hello"</div>'


def test_text_template_does_not_escape_quotes():
    name = '"world"'
    tag = div() >> t"hello {name}"
    assert str(tag) == '<div>hello "world"</div>'


def test_attribute_value_escapes_quotes():
    tag = div(title='He said "hi"')
    assert str(tag) == '<div title="He said &quot;hi&quot;"></div>'


def test_attribute_template_escapes_quotes():
    val = '"quoted"'
    tag = div(title=t"say {val}")
    assert str(tag) == '<div title="say &quot;quoted&quot;"></div>'


def test_render_boolean_attribute_true():
    tag = button(disabled=True) >> "Click"
    assert str(tag) == "<button disabled>Click</button>"


def test_render_boolean_attribute_false():
    tag = button(disabled=False) >> "Click"
    assert str(tag) == "<button>Click</button>"


def test_render_attribute_none_omitted():
    tag = div(id=None) >> "hi"
    assert str(tag) == "<div>hi</div>"


def test_comment_render():
    assert str(Comment("hello")) == "<!--hello-->"


def test_comment_in_tree():
    tag = div() >> Comment("note")
    assert str(tag) == "<div><!--note--></div>"


def test_comment_escapes_double_dash():
    assert str(Comment("bad-->stuff")) == "<!--bad- ->stuff-->"


def test_comment_escapes_double_dash_middle():
    assert str(Comment("a--b")) == "<!--a- -b-->"


def test_comment_clone():
    c = Comment("x")
    clone = c.clone_node()
    assert isinstance(clone, Comment)
    assert clone is not c


def test_comment_no_children():
    with pytest.raises(ValueError, match="Cannot add children"):
        Comment("x").append_child(Comment("y"))


def test_text_content_escapes_html():
    tag = div() >> "<script>alert(1)</script>"
    assert str(tag) == "<div>&lt;script&gt;alert(1)&lt;/script&gt;</div>"


def test_attribute_value_escapes_html():
    tag = div(id='"><script>alert(1)</script>')
    assert "<script>" not in str(tag)
    assert "&lt;script&gt;" in str(tag)


def test_template_interpolation_escapes_html():
    user_input = "<img onerror=alert(1)>"
    tag = div() >> t"{user_input}"
    assert str(tag) == "<div>&lt;img onerror=alert(1)&gt;</div>"


def test_template_attribute_escapes_html():
    evil = '"><script>alert(1)</script>'
    tag = div(id=t"{evil}")
    assert "<script>" not in str(tag)


def test_false_suppressed_in_children():
    tag = div() >> (False, "text")
    assert str(tag) == "<div>text</div>"


def test_false_suppressed_top_level():
    result = div() >> False
    assert result is None


def test_conditional_pattern_true():
    flag = True
    tag = div() >> (flag and (p() >> "yes"), "always")
    assert str(tag) == "<div><p>yes</p>always</div>"


def test_conditional_pattern_false():
    flag = False
    tag = div() >> (flag and (p() >> "yes"), "always")
    assert str(tag) == "<div>always</div>"


def test_false_in_lazy_return():
    tag = div() >> Lazy(lambda: False)
    assert str(tag) == "<div></div>"


def test_none_still_suppressed():
    tag = div() >> (None, "text")
    assert str(tag) == "<div>text</div>"
    assert div() >> None is None


def test_zero_not_suppressed():
    node = Node()
    with pytest.raises(ValueError, match="Unsupported type"):
        _flatten_into(node, (0,))


def test_empty_string_not_suppressed():
    tag = div() >> ""
    assert str(tag) == "<div></div>"


def test_fragment_repr():
    d = div(id="test")
    f = Fragment(d, d)
    assert "Fragment(" in repr(f)


async def test_fragment_stream():
    f = div() >> (p() >> "hello", p() >> "world")
    chunks = [chunk async for chunk in f.stream()]
    assert "".join(chunks) == "<div><p>hello</p><p>world</p></div>"


async def test_fragment_stream_with_args():
    title = Var("title")
    f = div() >> t"{title}"
    chunks = [chunk async for chunk in f.stream(args={"title": "hi"})]
    assert "".join(chunks) == "<div>hi</div>"


def test_attribute_numeric_value():
    tag = div(tabindex=0)
    assert str(tag) == '<div tabindex="0"></div>'


def test_attribute_numeric_value_escapes():
    tag = div(data_value=42)
    assert str(tag) == '<div data-value="42"></div>'
