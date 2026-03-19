from conftest import root

from shifthtml import Element, div, li, p, shift, span


def test_clone_node_shallow():
    f = shift(div(id="original") >> p >> "child")
    clone = root(f).clone_node()
    assert isinstance(clone, Element)
    assert clone is not root(f)
    assert clone["id"] == "original"
    assert len(clone.children) == 0


def test_clone_node_deep():
    f = shift(div(id="original") >> p >> span >> "text")
    clone = root(f).clone_node(deep=True)
    assert isinstance(clone, Element)
    assert clone is not root(f)
    assert clone["id"] == "original"
    assert len(clone.children) == 1
    assert str(shift(clone)) == '<div id="original"><p><span>text</span></p></div>'


def test_clone_node_no_parent():
    f = shift(div(id="test") >> p >> "child")
    clone = root(f).clone_node(deep=True)
    assert clone.parent_node is None


def test_clone_node_independent():
    f = shift(div(classname="original"))
    clone = root(f).clone_node()
    assert isinstance(clone, Element)
    clone["class"] = "clone"
    assert root(f)["class"] == "original"
    assert clone["class"] == "clone"


def test_clone_node_template_reuse():
    template = li(classname="item")
    items = [shift(template.clone_node() >> f"Item {i}") for i in range(3)]
    result = "".join(str(item) for item in items)
    assert result == '<li class="item">Item 0</li><li class="item">Item 1</li><li class="item">Item 2</li>'
