import pytest
from conftest import root

from shifthtml import div, h1, shift


def test_element_attributes_are_plain_dict():
    tag = div(id="main", classname="container")
    fragment = shift(tag)
    el = root(fragment)
    assert el.attributes["id"] == "main"
    assert el.attributes["class"] == "container"


def test_getitem():
    el = div(id="test")
    fragment = shift(el)
    r = root(fragment)
    assert r["id"] == "test"
    with pytest.raises(KeyError):
        r["missing"]


def test_setitem():
    el = div()
    fragment = shift(el)
    r = root(fragment)
    r["id"] = "new"
    assert r["id"] == "new"
    assert str(fragment) == '<div id="new"></div>'


def test_contains():
    el = div(id="test")
    fragment = shift(el)
    r = root(fragment)
    assert "id" in r
    assert "class" not in r


def test_delitem():
    el = div(id="test", classname="box")
    fragment = shift(el)
    r = root(fragment)
    del r["id"]
    assert "id" not in r
    assert "class" in r


def test_attributes_render_correctly():
    tag = shift(h1(id="hello", classname="bighead") >> "Hello")
    assert str(tag) == '<h1 id="hello" class="bighead">Hello</h1>'


def test_dict_attribute_names_lowercased():
    el = div({"ID": "main", "Data-TestId": "foo"})
    f = shift(el)
    assert root(f)["id"] == "main"
    assert root(f)["data-testid"] == "foo"
    assert str(f) == '<div id="main" data-testid="foo"></div>'


def test_setitem_lowercased():
    el = div()
    f = shift(el)
    root(f)["Data-Value"] = "42"
    assert root(f)["data-value"] == "42"
    assert "Data-Value" in root(f)


def test_getitem_case_insensitive():
    el = div(id="test")
    f = shift(el)
    assert root(f)["ID"] == "test"
    assert root(f)["Id"] == "test"


def test_contains_case_insensitive():
    el = div(id="test")
    f = shift(el)
    assert "ID" in root(f)
    assert "Id" in root(f)


def test_delitem_case_insensitive():
    el = div(id="test")
    f = shift(el)
    del root(f)["ID"]
    assert "id" not in root(f)


def test_keyword_attribute_names_lowercased():
    el = div(data_TestId="foo")
    f = shift(el)
    assert root(f)["data-testid"] == "foo"


def test_contains_non_string_returns_false():
    el = div(id="test")
    f = shift(el)
    assert (42 in root(f)) is False
