import pytest

from shifthtml import div, h1


def test_element_attributes_are_plain_dict():
    el = div(id="main", class_="container")
    assert el.attributes["id"] == "main"
    assert el.attributes["class"] == "container"


def test_getitem():
    el = div(id="test")
    assert el["id"] == "test"
    with pytest.raises(KeyError):
        el["missing"]


def test_setitem():
    el = div()
    el["id"] = "new"
    assert el["id"] == "new"
    assert str(el) == '<div id="new"></div>'


def test_contains():
    el = div(id="test")
    assert "id" in el
    assert "class" not in el


def test_delitem():
    el = div(id="test", class_="box")
    del el["id"]
    assert "id" not in el
    assert "class" in el


def test_attributes_render_correctly():
    tag = h1(id="hello", class_="bighead") >> "Hello"
    assert str(tag) == '<h1 id="hello" class="bighead">Hello</h1>'


def test_dict_attribute_names_lowercased():
    el = div({"ID": "main", "Data-TestId": "foo"})
    assert el["id"] == "main"
    assert el["data-testid"] == "foo"
    assert str(el) == '<div id="main" data-testid="foo"></div>'


def test_setitem_lowercased():
    el = div()
    el["Data-Value"] = "42"
    assert el["data-value"] == "42"
    assert "Data-Value" in el


def test_getitem_case_insensitive():
    el = div(id="test")
    assert el["ID"] == "test"
    assert el["Id"] == "test"


def test_contains_case_insensitive():
    el = div(id="test")
    assert "ID" in el
    assert "Id" in el


def test_delitem_case_insensitive():
    el = div(id="test")
    del el["ID"]
    assert "id" not in el


def test_keyword_attribute_names_lowercased():
    el = div(data_TestId="foo")
    assert el["data-testid"] == "foo"


def test_contains_non_string_returns_false():
    el = div(id="test")
    assert (42 in el) is False


def test_attribute_template_value():
    val = "dynamic"
    el = div(id=t"{val}")
    assert str(el) == '<div id="dynamic"></div>'


def test_attribute_empty_string():
    el = div(id="")
    assert str(el) == '<div id=""></div>'


def test_boolean_attributes():
    el = div() >> "x"
    el.root["hidden"] = True
    assert str(el) == "<div hidden>x</div>"
    el.root["hidden"] = False
    assert str(el) == "<div>x</div>"
