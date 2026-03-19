import pytest

from shifthtml import div, h1, shift


def test_element_attributes_are_plain_dict():
    tag = div(id="main", classname="container")
    fragment = shift(tag)
    el = fragment.root
    assert el.attributes["id"] == "main"
    assert el.attributes["class"] == "container"


def test_getitem():
    el = div(id="test")
    fragment = shift(el)
    root = fragment.root
    assert root["id"] == "test"
    with pytest.raises(KeyError):
        root["missing"]


def test_setitem():
    el = div()
    fragment = shift(el)
    root = fragment.root
    root["id"] = "new"
    assert root["id"] == "new"
    assert str(fragment) == '<div id="new"></div>'


def test_contains():
    el = div(id="test")
    fragment = shift(el)
    root = fragment.root
    assert "id" in root
    assert "class" not in root


def test_delitem():
    el = div(id="test", classname="box")
    fragment = shift(el)
    root = fragment.root
    del root["id"]
    assert "id" not in root
    assert "class" in root


def test_attributes_render_correctly():
    tag = shift(h1(id="hello", classname="bighead") >> "Hello")
    assert str(tag) == '<h1 id="hello" class="bighead">Hello</h1>'


def test_dict_attribute_names_lowercased():
    el = div({"ID": "main", "Data-TestId": "foo"})
    f = shift(el)
    assert f.root["id"] == "main"
    assert f.root["data-testid"] == "foo"
    assert str(f) == '<div id="main" data-testid="foo"></div>'


def test_setitem_lowercased():
    el = div()
    f = shift(el)
    f.root["Data-Value"] = "42"
    assert f.root["data-value"] == "42"
    assert "Data-Value" in f.root


def test_getitem_case_insensitive():
    el = div(id="test")
    f = shift(el)
    assert f.root["ID"] == "test"
    assert f.root["Id"] == "test"


def test_contains_case_insensitive():
    el = div(id="test")
    f = shift(el)
    assert "ID" in f.root
    assert "Id" in f.root


def test_delitem_case_insensitive():
    el = div(id="test")
    f = shift(el)
    del f.root["ID"]
    assert "id" not in f.root


def test_keyword_attribute_names_lowercased():
    el = div(data_TestId="foo")
    f = shift(el)
    assert f.root["data-testid"] == "foo"
