from shifthtml import div
from shifthtml.mappings import StyleMap


def test_style_set_get_via_attr():
    style = StyleMap()
    style.color = "red"
    assert style.color == "red"


def test_style_snake_to_kebab():
    style = StyleMap()
    style.font_size = "16px"
    assert style["font-size"] == "16px"
    assert style.font_size == "16px"


def test_style_delete_via_attr():
    style = StyleMap()
    style.color = "red"
    del style.color
    assert style.color == ""


def test_style_setitem_getitem():
    style = StyleMap()
    style["color"] = "red"
    style["font-size"] = "16px"
    assert style.css_text == "color: red; font-size: 16px"


def test_style_delitem():
    style = StyleMap()
    style["color"] = "red"
    del style["color"]
    assert "color" not in style


def test_style_contains():
    style = StyleMap()
    style["color"] = "red"
    assert "color" in style
    assert "font-size" not in style


def test_style_iter():
    style = StyleMap()
    style["color"] = "red"
    style["font-size"] = "16px"
    assert list(style) == ["color", "font-size"]


def test_css_text_getter():
    style = StyleMap()
    style["color"] = "red"
    style["font-size"] = "16px"
    assert style.css_text == "color: red; font-size: 16px"


def test_css_text_setter():
    style = StyleMap()
    style.css_text = "color: red; font-size: 16px"
    assert style["color"] == "red"
    assert style["font-size"] == "16px"


def test_css_text_setter_clears_existing():
    style = StyleMap()
    style["background"] = "blue"
    style.css_text = "color: red"
    assert "background" not in style
    assert style["color"] == "red"


def test_pop():
    style = StyleMap()
    style["color"] = "red"
    removed = style.pop("color")
    assert removed == "red"
    assert "color" not in style


def test_pop_missing():
    style = StyleMap()
    assert style.pop("color") == ""


def test_len():
    style = StyleMap()
    assert len(style) == 0
    style.color = "red"
    assert len(style) == 1
    style.font_size = "16px"
    assert len(style) == 2


def test_str():
    style = StyleMap()
    style["color"] = "red"
    style["font-size"] = "16px"
    assert str(style) == "color: red; font-size: 16px"


def test_get_missing_property():
    style = StyleMap()
    assert style.color == ""


def test_element_style_property():
    el = div()
    el.style.color = "red"
    el.style.font_size = "16px"
    assert str(el) == '<div style="color: red; font-size: 16px"></div>'


def test_element_style_from_existing_attribute():
    el = div(style="color: red")
    assert el.style["color"] == "red"
    el.style.font_size = "16px"
    assert str(el) == '<div style="color: red; font-size: 16px"></div>'


def test_element_style_not_materialized_without_access():
    el = div(id="test")
    assert str(el) == '<div id="test"></div>'


def test_render_twice_consistent():
    el = div()
    el.style.color = "red"
    first = str(el)
    second = str(el)
    assert first == second
    assert "style" not in el.attributes
