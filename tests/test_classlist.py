from conftest import root

from shifthtml import div, shift


def test_classlist_add():
    el = div()
    f = shift(el)
    root(f).class_list.add("foo", "bar")
    assert str(f) == '<div class="foo bar"></div>'


def test_classlist_add_no_duplicates():
    el = div(class_="foo")
    f = shift(el)
    root(f).class_list.add("foo", "bar")
    assert str(f) == '<div class="foo bar"></div>'


def test_classlist_remove():
    el = div(class_="foo bar baz")
    f = shift(el)
    root(f).class_list.remove("bar")
    assert str(f) == '<div class="foo baz"></div>'


def test_classlist_remove_multiple():
    el = div(class_="foo bar baz")
    f = shift(el)
    root(f).class_list.remove("foo", "baz")
    assert str(f) == '<div class="bar"></div>'


def test_classlist_toggle_on():
    el = div()
    f = shift(el)
    result = root(f).class_list.toggle("active")
    assert result is True
    assert str(f) == '<div class="active"></div>'


def test_classlist_toggle_off():
    el = div(class_="active")
    f = shift(el)
    result = root(f).class_list.toggle("active")
    assert result is False
    assert str(f) == '<div class=""></div>'


def test_classlist_toggle_force_true():
    el = div(class_="active")
    f = shift(el)
    result = root(f).class_list.toggle("active", True)
    assert result is True
    assert "active" in str(f)


def test_classlist_toggle_force_false():
    el = div()
    f = shift(el)
    result = root(f).class_list.toggle("active", False)
    assert result is False
    assert "active" not in str(f)


def test_classlist_contains():
    el = div(class_="foo bar")
    f = shift(el)
    assert "foo" in root(f).class_list
    assert "baz" not in root(f).class_list


def test_classlist_replace():
    el = div(class_="old-class other")
    f = shift(el)
    result = root(f).class_list.replace("old-class", "new-class")
    assert result is True
    assert str(f) == '<div class="new-class other"></div>'


def test_classlist_replace_missing():
    el = div(class_="other")
    f = shift(el)
    result = root(f).class_list.replace("missing", "new")
    assert result is False


def test_classlist_len():
    el = div(class_="a b c")
    f = shift(el)
    assert len(root(f).class_list) == 3


def test_classlist_str():
    el = div(class_="a b c")
    f = shift(el)
    assert str(root(f).class_list) == "a b c"


def test_classlist_iteration():
    el = div(class_="a b c")
    f = shift(el)
    assert list(root(f).class_list) == ["a", "b", "c"]


def test_classlist_in_operator():
    el = div(class_="foo bar")
    f = shift(el)
    assert "foo" in root(f).class_list
    assert "baz" not in root(f).class_list


def test_classlist_from_list_attribute():
    el = div(class_=["foo", "bar", "baz"])
    f = shift(el)
    root(f).class_list.remove("bar")
    assert str(f) == '<div class="foo baz"></div>'
