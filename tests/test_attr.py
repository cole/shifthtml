from shifthtml import div, h1, shift


def test_element_attributes_are_plain_dict():
    tag = div(id="main", classname="container")
    fragment = shift(tag)
    el = fragment.root
    assert el.attributes["id"] == "main"
    assert el.attributes["class"] == "container"


def test_get_attribute():
    el = div(id="test")
    fragment = shift(el)
    root = fragment.root
    assert root.get_attribute("id") == "test"
    assert root.get_attribute("missing") is None


def test_set_attribute():
    el = div()
    fragment = shift(el)
    root = fragment.root
    root.set_attribute("id", "new")
    assert root.get_attribute("id") == "new"
    assert str(fragment) == '<div id="new"></div>'


def test_has_attribute():
    el = div(id="test")
    fragment = shift(el)
    root = fragment.root
    assert root.has_attribute("id") is True
    assert root.has_attribute("class") is False


def test_remove_attribute():
    el = div(id="test", classname="box")
    fragment = shift(el)
    root = fragment.root
    root.remove_attribute("id")
    assert root.has_attribute("id") is False
    assert root.has_attribute("class") is True


def test_attributes_render_correctly():
    tag = shift(h1(id="hello", classname="bighead") >> "Hello")
    assert str(tag) == '<h1 id="hello" class="bighead">Hello</h1>'
