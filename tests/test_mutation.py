import pytest

from shifthtml import div, h1, li, p, span, ul
from shifthtml.tree import TreeNode


def test_remove():
    parent = div()
    c1 = (p >> "keep").root
    c2 = (p >> "remove").root
    c3 = (p >> "keep2").root
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
    f = div() >> (p >> "old",)
    old = f.root.first_child
    assert isinstance(old, TreeNode)
    new = (span >> "new").root
    old.replace_with(new)
    assert str(f) == "<div><span>new</span></div>"


def test_replace_with_multiple():
    f = div() >> (p >> "target",)
    target = f.root.first_child
    assert isinstance(target, TreeNode)
    a = (span >> "a").root
    b = (span >> "b").root
    target.replace_with(a, b)
    assert str(f) == "<div><span>a</span><span>b</span></div>"


def test_replace_with_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.replace_with(p())


def test_before():
    f = ul() >> (li >> "second",)
    second = f.root.first_child
    assert isinstance(second, TreeNode)
    first = (li >> "first").root
    second.before(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_before_multiple():
    f = ul() >> (li >> "third",)
    third = f.root.first_child
    assert isinstance(third, TreeNode)
    first = (li >> "first").root
    second = (li >> "second").root
    third.before(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_before_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.before(p())


def test_after():
    f = ul() >> (li >> "first",)
    first = f.root.first_child
    assert isinstance(first, TreeNode)
    second = (li >> "second").root
    first.after(second)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_after_multiple():
    f = ul() >> (li >> "first",)
    first = f.root.first_child
    assert isinstance(first, TreeNode)
    second = (li >> "second").root
    third = (li >> "third").root
    first.after(second, third)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_after_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.after(p())


def test_prepend():
    f = ul() >> (li >> "second",)
    first = (li >> "first").root
    f.root.prepend(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_prepend_multiple():
    f = ul() >> (li >> "third",)
    first = (li >> "first").root
    second = (li >> "second").root
    f.root.prepend(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_prepend_to_empty():
    el = ul()
    item = (li >> "only").root
    el.prepend(item)
    assert str(el) == "<ul><li>only</li></ul>"


def test_insert_before():
    parent = ul()
    first = (li >> "first").root
    third = (li >> "third").root
    parent.append_child(first)
    parent.append_child(third)
    second = (li >> "second").root
    parent.insert_before(second, third)
    assert str(parent) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_insert_before_invalid_reference():
    f = ul() >> (li >> "first",)
    orphan = (li >> "orphan").root
    new = (li >> "new").root
    with pytest.raises(ValueError, match="not a child"):
        f.root.insert_before(new, orphan)


def test_replace_child():
    f = div() >> (p >> "old",)
    old = f.root.first_child
    assert isinstance(old, TreeNode)
    new = (span >> "new").root
    returned = f.root.replace_child(new, old)
    assert returned is old
    assert old.parent_node is None
    assert str(f) == "<div><span>new</span></div>"


def test_replace_child_not_found():
    f = div() >> (p >> "child",)
    orphan = p()
    new = span()
    with pytest.raises(ValueError, match="not a child"):
        f.root.replace_child(new, orphan)


def test_contains():
    f = div() >> p >> span >> "deep"
    root = f.root
    first = root.first_child
    assert isinstance(first, TreeNode)
    deep_span = first.first_child
    assert isinstance(deep_span, TreeNode)
    assert root.contains(deep_span) is True
    assert root.contains(root) is True

    orphan = h1()
    assert root.contains(orphan) is False


def test_mutation_preserves_siblings():
    parent = ul()
    a = (li >> "a").root
    b = (li >> "b").root
    c = (li >> "c").root
    parent.append_child(a)
    parent.append_child(b)
    parent.append_child(c)
    b.remove()
    assert a.next_sibling is c
    assert c.previous_sibling is a
