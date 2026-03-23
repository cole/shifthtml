from conftest import root

from shifthtml import Element, body, div, h1, li, p, span


def test_clone_node_shallow():
    f = div(id="original") >> p >> "child"
    clone = root(f).clone_node()
    assert isinstance(clone, Element)
    assert clone is not root(f)
    assert clone["id"] == "original"
    assert len(clone.children) == 0


def test_clone_node_deep():
    f = div(id="original") >> p >> span >> "text"
    clone = root(f).clone_node(deep=True)
    assert isinstance(clone, Element)
    assert clone is not root(f)
    assert clone["id"] == "original"
    assert len(clone.children) == 1
    assert str(clone) == '<div id="original"><p><span>text</span></p></div>'


def test_clone_node_no_parent():
    f = div(id="test") >> p >> "child"
    clone = root(f).clone_node(deep=True)
    assert clone.parent_node is None


def test_clone_node_independent():
    el = div(class_="original")
    clone = el.clone_node()
    assert isinstance(clone, Element)
    clone["class"] = "clone"
    assert el["class"] == "original"
    assert clone["class"] == "clone"


def test_clone_node_template_reuse():
    template = li(class_="item")
    items = [template.clone_node() >> f"Item {i}" for i in range(3)]
    result = "".join(str(item) for item in items)
    assert result == '<li class="item">Item 0</li><li class="item">Item 1</li><li class="item">Item 2</li>'


def test_fragment_append_fragment_with_tuple():
    inner = div(id="inner") >> (h1 >> "title", span >> "content")
    result = body >> inner
    assert str(result) == '<body><div id="inner"><h1>title</h1><span>content</span></div></body>'


def test_deep_clone_with_flattened_children():
    f = div >> (span >> "a", span >> "b")
    clone = root(f).clone_node(deep=True)
    assert str(clone) == "<div><span>a</span><span>b</span></div>"
