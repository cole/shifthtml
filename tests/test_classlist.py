from shifthtml import div, shift


def test_classlist_add():
    el = div()
    f = shift(el)
    f.root.class_list.add("foo", "bar")
    assert str(f) == '<div class="foo bar"></div>'


def test_classlist_add_no_duplicates():
    el = div(classname="foo")
    f = shift(el)
    f.root.class_list.add("foo", "bar")
    assert str(f) == '<div class="foo bar"></div>'


def test_classlist_remove():
    el = div(classname="foo bar baz")
    f = shift(el)
    f.root.class_list.remove("bar")
    assert str(f) == '<div class="foo baz"></div>'


def test_classlist_remove_multiple():
    el = div(classname="foo bar baz")
    f = shift(el)
    f.root.class_list.remove("foo", "baz")
    assert str(f) == '<div class="bar"></div>'


def test_classlist_toggle_on():
    el = div()
    f = shift(el)
    result = f.root.class_list.toggle("active")
    assert result is True
    assert str(f) == '<div class="active"></div>'


def test_classlist_toggle_off():
    el = div(classname="active")
    f = shift(el)
    result = f.root.class_list.toggle("active")
    assert result is False
    assert str(f) == '<div class=""></div>'


def test_classlist_toggle_force_true():
    el = div(classname="active")
    f = shift(el)
    result = f.root.class_list.toggle("active", True)
    assert result is True
    assert "active" in str(f)


def test_classlist_toggle_force_false():
    el = div()
    f = shift(el)
    result = f.root.class_list.toggle("active", False)
    assert result is False
    assert "active" not in str(f)


def test_classlist_contains():
    el = div(classname="foo bar")
    f = shift(el)
    assert "foo" in f.root.class_list
    assert "baz" not in f.root.class_list


def test_classlist_replace():
    el = div(classname="old-class other")
    f = shift(el)
    result = f.root.class_list.replace("old-class", "new-class")
    assert result is True
    assert str(f) == '<div class="new-class other"></div>'


def test_classlist_replace_missing():
    el = div(classname="other")
    f = shift(el)
    result = f.root.class_list.replace("missing", "new")
    assert result is False


def test_classlist_len():
    el = div(classname="a b c")
    f = shift(el)
    assert len(f.root.class_list) == 3


def test_classlist_str():
    el = div(classname="a b c")
    f = shift(el)
    assert str(f.root.class_list) == "a b c"


def test_classlist_iteration():
    el = div(classname="a b c")
    f = shift(el)
    assert list(f.root.class_list) == ["a", "b", "c"]


def test_classlist_in_operator():
    el = div(classname="foo bar")
    f = shift(el)
    assert "foo" in f.root.class_list
    assert "baz" not in f.root.class_list


def test_classlist_from_list_attribute():
    el = div(classname=["foo", "bar", "baz"])
    f = shift(el)
    f.root.class_list.remove("bar")
    assert str(f) == '<div class="foo baz"></div>'
