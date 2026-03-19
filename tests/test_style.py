from shifthtml import div, shift
from shifthtml.style import CSSStyleDeclaration


def test_css_style_declaration_set_get():
    style = CSSStyleDeclaration()
    style.color = "red"
    assert style.color == "red"


def test_css_style_declaration_snake_to_kebab():
    style = CSSStyleDeclaration()
    style.font_size = "16px"
    assert style.get_property_value("font-size") == "16px"
    assert style.font_size == "16px"


def test_css_style_declaration_delete():
    style = CSSStyleDeclaration()
    style.color = "red"
    del style.color
    assert style.color == ""


def test_css_text_getter():
    style = CSSStyleDeclaration()
    style.set_property("color", "red")
    style.set_property("font-size", "16px")
    assert style.css_text == "color: red; font-size: 16px"


def test_css_text_setter():
    style = CSSStyleDeclaration()
    style.css_text = "color: red; font-size: 16px"
    assert style.get_property_value("color") == "red"
    assert style.get_property_value("font-size") == "16px"


def test_css_text_setter_clears_existing():
    style = CSSStyleDeclaration()
    style.set_property("background", "blue")
    style.css_text = "color: red"
    assert style.get_property_value("background") == ""
    assert style.get_property_value("color") == "red"


def test_remove_property():
    style = CSSStyleDeclaration()
    style.set_property("color", "red")
    removed = style.remove_property("color")
    assert removed == "red"
    assert style.get_property_value("color") == ""


def test_remove_property_missing():
    style = CSSStyleDeclaration()
    assert style.remove_property("color") == ""


def test_length():
    style = CSSStyleDeclaration()
    assert style.length == 0
    style.color = "red"
    assert style.length == 1
    style.font_size = "16px"
    assert style.length == 2


def test_get_missing_property():
    style = CSSStyleDeclaration()
    assert style.color == ""


def test_element_style_property():
    el = div()
    fragment = shift(el)
    root = fragment.root
    root.style.color = "red"
    root.style.font_size = "16px"
    assert str(fragment) == '<div style="color: red; font-size: 16px"></div>'


def test_element_style_from_existing_attribute():
    el = div(style="color: red")
    fragment = shift(el)
    root = fragment.root
    assert root.style.get_property_value("color") == "red"
    root.style.font_size = "16px"
    assert str(fragment) == '<div style="color: red; font-size: 16px"></div>'


def test_element_style_not_materialized_without_access():
    el = div(id="test")
    fragment = shift(el)
    assert str(fragment) == '<div id="test"></div>'
