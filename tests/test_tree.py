import copy
from collections.abc import AsyncGenerator, Generator

import pytest

from shifthtml import div, h1, li, p, span, ul
from shifthtml.rendering import RenderContext
from shifthtml.tree import Fragment, Node


class SimpleNode(Node):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __replace__(self, /, **changes):
        return SimpleNode(self.value)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield self.value

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield self.value


def test_node_depth():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node1.append_child(node2)
    node2.append_child(node3)

    assert node1.children == [node2]
    assert node2.parent_node is node1
    assert node3.parent_node is node2
    assert node2.children == [node3]
    assert list(node1) == [node2]


def test_node_breadth():
    node1 = SimpleNode("1")
    node2_1 = SimpleNode("2.1")
    node2_2 = SimpleNode("2.2")
    node2_3 = SimpleNode("2.3")
    node3_1 = SimpleNode("3.1")
    node3_2 = SimpleNode("3.2")
    node3_3 = SimpleNode("3.3")
    node3_4 = SimpleNode("3.4")

    node1.append_child(node2_1)
    node1.append_child(node2_2)
    node1.append_child(node2_3)
    node2_2.append_child(node3_1)
    node2_2.append_child(node3_2)
    node2_3.append_child(node3_3)
    node2_3.append_child(node3_4)

    assert node1.children == [node2_1, node2_2, node2_3]
    assert node2_1.children == []
    assert node2_2.children == [node3_1, node3_2]
    assert node2_3.children == [node3_3, node3_4]
    assert node2_1.parent_node is node1
    assert node2_2.parent_node is node1
    assert node2_3.parent_node is node1
    assert node3_1.parent_node is node2_2
    assert node3_2.parent_node is node2_2
    assert node3_3.parent_node is node2_3
    assert node3_4.parent_node is node2_3

    assert list(node1) == [node2_1, node2_2, node2_3]

    assert [n.value for n in node1.walk() if isinstance(n, SimpleNode)] == [
        "1",
        "2.1",
        "2.2",
        "3.1",
        "3.2",
        "2.3",
        "3.3",
        "3.4",
    ]


def test_node_child_of_self():
    node1 = SimpleNode("1")
    with pytest.raises(ValueError, match="Can't make a node a child of itself"):
        node1.append_child(node1)


def test_node_accepts_string_children():
    node = SimpleNode("parent")
    node.append_child("text child")
    assert node.children == ["text child"]


def test_node_add_unknown_type():
    with pytest.raises(ValueError, match="Expected a Node, str, or Template"):
        SimpleNode("test").append_child(42)  # ty: ignore[invalid-argument-type]


def test_fragment_append_node():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node4 = SimpleNode("4")
    tree = Fragment(node1, node1)

    tree2 = copy.deepcopy(tree)
    tree2.append(node2)
    tree3 = copy.deepcopy(tree2)
    tree3.append(node3)

    tree4 = copy.deepcopy(tree2)
    tree4.append(node4)

    assert tree is not tree2
    assert tree.root is node1
    assert tree.append_pointer is node1
    assert isinstance(tree2.root, SimpleNode) and tree2.root.value == node1.value
    assert isinstance(tree2.append_pointer, SimpleNode) and tree2.append_pointer.value == node2.value
    assert isinstance(tree3.root, SimpleNode) and tree3.root.value == node1.value
    assert isinstance(tree3.append_pointer, SimpleNode) and tree3.append_pointer.value == node3.value
    assert isinstance(tree4.root, SimpleNode) and tree4.root.value == node1.value
    assert isinstance(tree4.append_pointer, SimpleNode) and tree4.append_pointer.value == node4.value

    # Verify tree structure
    assert len(tree.root.children) == 0
    assert len(tree2.root.children) == 1
    assert tree2.root.children[0] is tree2.append_pointer
    assert len(tree3.root.children) == 1
    child3 = tree3.root.children[0]
    assert isinstance(child3, Node) and child3.children[0] is tree3.append_pointer
    assert len(tree4.root.children) == 1
    child4 = tree4.root.children[0]
    assert isinstance(child4, Node) and child4.children[0] is tree4.append_pointer


def test_fragment_append_fragment():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node4 = SimpleNode("4")
    tree1 = Fragment(node1, node1)
    tree1.append(node2)
    tree2 = Fragment(node3, node3)
    tree2.append(node4)

    tree1.append(tree2)

    # Verify: node1 -> node2 -> node3 -> node4
    assert node1.children[0] is node2
    c = node2.children[0]
    assert isinstance(c, SimpleNode) and c.value == "3"
    assert isinstance(c.children[0], SimpleNode) and c.children[0].value == "4"


def test_fragment_rshift_mutates_in_place():
    d = div()
    f = Fragment(d, d)
    f2 = f >> "text"
    assert f2 is f
    assert "text" in str(f)


# -- DOM mutation methods --


def test_remove():
    parent = div()
    c1 = (p() >> "keep").root
    c2 = (p() >> "remove").root
    c3 = (p() >> "keep2").root
    parent.append_child(c1)
    parent.append_child(c2)
    parent.append_child(c3)
    c2.remove()
    assert str(parent) == "<div><p>keep</p><p>keep2</p></div>"


def test_remove_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.remove()


def test_replace_with_single():
    f = div() >> (p() >> "old",)
    old = f.root.first_child
    assert isinstance(old, Node)
    new = (span() >> "new").root
    old.replace_with(new)
    assert str(f) == "<div><span>new</span></div>"


def test_replace_with_multiple():
    f = div() >> (p() >> "target",)
    target = f.root.first_child
    assert isinstance(target, Node)
    a = (span() >> "a").root
    b = (span() >> "b").root
    target.replace_with(a, b)
    assert str(f) == "<div><span>a</span><span>b</span></div>"


def test_replace_with_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.replace_with(p())


def test_before():
    f = ul() >> (li() >> "second",)
    second = f.root.first_child
    assert isinstance(second, Node)
    first = (li() >> "first").root
    second.before(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_before_multiple():
    f = ul() >> (li() >> "third",)
    third = f.root.first_child
    assert isinstance(third, Node)
    first = (li() >> "first").root
    second = (li() >> "second").root
    third.before(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_before_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.before(p())


def test_after():
    f = ul() >> (li() >> "first",)
    first = f.root.first_child
    assert isinstance(first, Node)
    second = (li() >> "second").root
    first.after(second)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_after_multiple():
    f = ul() >> (li() >> "first",)
    first = f.root.first_child
    assert isinstance(first, Node)
    second = (li() >> "second").root
    third = (li() >> "third").root
    first.after(second, third)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_after_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.after(p())


def test_prepend():
    f = ul() >> (li() >> "second",)
    first = (li() >> "first").root
    f.root.prepend(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_prepend_multiple():
    f = ul() >> (li() >> "third",)
    first = (li() >> "first").root
    second = (li() >> "second").root
    f.root.prepend(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_prepend_to_empty():
    el = ul()
    item = (li() >> "only").root
    el.prepend(item)
    assert str(el) == "<ul><li>only</li></ul>"


def test_insert_before():
    parent = ul()
    first = (li() >> "first").root
    third = (li() >> "third").root
    parent.append_child(first)
    parent.append_child(third)
    second = (li() >> "second").root
    parent.insert_before(second, third)
    assert str(parent) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_insert_before_invalid_reference():
    f = ul() >> (li() >> "first",)
    orphan = (li() >> "orphan").root
    new = (li() >> "new").root
    with pytest.raises(ValueError, match="not a child"):
        f.root.insert_before(new, orphan)


def test_replace_child():
    f = div() >> (p() >> "old",)
    old = f.root.first_child
    assert isinstance(old, Node)
    new = (span() >> "new").root
    returned = f.root.replace_child(new, old)
    assert returned is old
    assert old.parent_node is None
    assert str(f) == "<div><span>new</span></div>"


def test_replace_child_not_found():
    f = div() >> (p() >> "child",)
    orphan = p()
    new = span()
    with pytest.raises(ValueError, match="not a child"):
        f.root.replace_child(new, orphan)


def test_contains():
    f = div() >> p() >> span() >> "deep"
    root = f.root
    first = root.first_child
    assert isinstance(first, Node)
    deep_span = first.first_child
    assert isinstance(deep_span, Node)
    assert root.contains(deep_span) is True
    assert root.contains(root) is True

    orphan = h1()
    assert root.contains(orphan) is False


def test_last_child():
    parent = div()
    a = (p() >> "a").root
    b = (p() >> "b").root
    parent.append_child(a)
    parent.append_child(b)
    assert parent.last_child is b


def test_last_child_empty():
    el = div()
    assert el.last_child is None


def test_first_child_empty():
    el = div()
    assert el.first_child is None


def test_previous_sibling():
    parent = ul()
    a = (li() >> "a").root
    b = (li() >> "b").root
    c = (li() >> "c").root
    parent.append_child(a)
    parent.append_child(b)
    parent.append_child(c)
    assert b.previous_sibling is a
    assert a.previous_sibling is None


def test_next_sibling():
    parent = ul()
    a = (li() >> "a").root
    b = (li() >> "b").root
    parent.append_child(a)
    parent.append_child(b)
    assert a.next_sibling is b
    assert b.next_sibling is None


def test_sibling_no_parent():
    el = div()
    assert el.next_sibling is None
    assert el.previous_sibling is None


def test_remove_child_direct():
    parent = div()
    child = (p() >> "x").root
    parent.append_child(child)
    parent.remove_child(child)
    assert child not in parent.children
    assert child.parent_node is None


def test_remove_child_not_found():
    parent = div()
    orphan = p()
    with pytest.raises(ValueError, match="not a child"):
        parent.remove_child(orphan)


def test_dom_mutation_preserves_siblings():
    parent = ul()
    a = (li() >> "a").root
    b = (li() >> "b").root
    c = (li() >> "c").root
    parent.append_child(a)
    parent.append_child(b)
    parent.append_child(c)
    b.remove()
    assert a.next_sibling is c
    assert c.previous_sibling is a
