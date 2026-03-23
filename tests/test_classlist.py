from shifthtml import div


def test_classlist_add():
    el = div()
    el.class_list.add("foo", "bar")
    assert str(el) == '<div class="foo bar"></div>'


def test_classlist_add_no_duplicates():
    el = div(class_="foo")
    el.class_list.add("foo", "bar")
    assert str(el) == '<div class="foo bar"></div>'


def test_classlist_remove():
    el = div(class_="foo bar baz")
    el.class_list.remove("bar")
    assert str(el) == '<div class="foo baz"></div>'


def test_classlist_remove_multiple():
    el = div(class_="foo bar baz")
    el.class_list.remove("foo", "baz")
    assert str(el) == '<div class="bar"></div>'


def test_classlist_toggle_on():
    el = div()
    result = el.class_list.toggle("active")
    assert result is True
    assert str(el) == '<div class="active"></div>'


def test_classlist_toggle_off():
    el = div(class_="active")
    result = el.class_list.toggle("active")
    assert result is False
    assert str(el) == '<div class=""></div>'


def test_classlist_toggle_force_true():
    el = div(class_="active")
    result = el.class_list.toggle("active", True)
    assert result is True
    assert "active" in str(el)


def test_classlist_toggle_force_false():
    el = div()
    result = el.class_list.toggle("active", False)
    assert result is False
    assert "active" not in str(el)


def test_classlist_contains():
    el = div(class_="foo bar")
    assert "foo" in el.class_list
    assert "baz" not in el.class_list


def test_classlist_replace():
    el = div(class_="old-class other")
    result = el.class_list.replace("old-class", "new-class")
    assert result is True
    assert str(el) == '<div class="new-class other"></div>'


def test_classlist_replace_missing():
    el = div(class_="other")
    result = el.class_list.replace("missing", "new")
    assert result is False


def test_classlist_len():
    el = div(class_="a b c")
    assert len(el.class_list) == 3


def test_classlist_str():
    el = div(class_="a b c")
    assert str(el.class_list) == "a b c"


def test_classlist_iteration():
    el = div(class_="a b c")
    assert list(el.class_list) == ["a", "b", "c"]


def test_classlist_in_operator():
    el = div(class_="foo bar")
    assert "foo" in el.class_list
    assert "baz" not in el.class_list


def test_classlist_from_list_attribute():
    el = div(class_=["foo", "bar", "baz"])
    el.class_list.remove("bar")
    assert str(el) == '<div class="foo baz"></div>'
