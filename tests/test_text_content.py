from conftest import root

from shifthtml import div, h1, p, shift, span


def test_text_content_simple():
    f = shift(p >> "hello")
    assert root(f).text_content == "hello"


def test_text_content_nested():
    f = shift(div() >> (p >> "Hello ", p >> (span >> "world")))
    assert root(f).text_content == "Hello world"


def test_text_content_deep():
    f = shift(div >> p >> span >> "deep")
    assert root(f).text_content == "deep"


def test_text_content_empty():
    f = shift(div())
    assert root(f).text_content == ""


def test_text_content_multiple_text_nodes():
    parent = div()
    parent.append_child(shift(h1 >> "Title").root)
    parent.append_child(shift(p >> "Body text").root)
    f = shift(parent)
    assert root(f).text_content == "TitleBody text"


def test_string_child_is_first_class():
    f = shift(span >> "just text")
    assert f.root.first_child == "just text"
    assert root(f).text_content == "just text"
