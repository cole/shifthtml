import pytest

from shifthtml import div, h1, li, p, shift, span, ul


def test_remove():
    parent = div()
    c1 = shift(p >> "keep").root
    c2 = shift(p >> "remove").root
    c3 = shift(p >> "keep2").root
    parent.append_child(c1)
    parent.append_child(c2)
    parent.append_child(c3)
    f = shift(parent)
    c2.remove()
    assert str(f) == "<div><p>keep</p><p>keep2</p></div>"


def test_remove_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.remove()


def test_replace_with_single():
    f = shift(div() >> (p >> "old",))
    old = f.root.first_child
    assert old is not None
    new = shift(span >> "new").root
    old.replace_with(new)
    assert str(f) == "<div><span>new</span></div>"


def test_replace_with_multiple():
    f = shift(div() >> (p >> "target",))
    target = f.root.first_child
    assert target is not None
    a = shift(span >> "a").root
    b = shift(span >> "b").root
    target.replace_with(a, b)
    assert str(f) == "<div><span>a</span><span>b</span></div>"


def test_replace_with_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.replace_with(p())


def test_before():
    f = shift(ul() >> (li >> "second",))
    second = f.root.first_child
    assert second is not None
    first = shift(li >> "first").root
    second.before(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_before_multiple():
    f = shift(ul() >> (li >> "third",))
    third = f.root.first_child
    assert third is not None
    first = shift(li >> "first").root
    second = shift(li >> "second").root
    third.before(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_before_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.before(p())


def test_after():
    f = shift(ul() >> (li >> "first",))
    first = f.root.first_child
    assert first is not None
    second = shift(li >> "second").root
    first.after(second)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_after_multiple():
    f = shift(ul() >> (li >> "first",))
    first = f.root.first_child
    assert first is not None
    second = shift(li >> "second").root
    third = shift(li >> "third").root
    first.after(second, third)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_after_no_parent():
    el = div()
    with pytest.raises(ValueError, match="no parent"):
        el.after(p())


def test_prepend():
    f = shift(ul() >> (li >> "second",))
    first = shift(li >> "first").root
    f.root.prepend(first)
    assert str(f) == "<ul><li>first</li><li>second</li></ul>"


def test_prepend_multiple():
    f = shift(ul() >> (li >> "third",))
    first = shift(li >> "first").root
    second = shift(li >> "second").root
    f.root.prepend(first, second)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_prepend_to_empty():
    f = shift(ul())
    item = shift(li >> "only").root
    f.root.prepend(item)
    assert str(f) == "<ul><li>only</li></ul>"


def test_insert_before():
    parent = ul()
    first = shift(li >> "first").root
    third = shift(li >> "third").root
    parent.append_child(first)
    parent.append_child(third)
    f = shift(parent)
    second = shift(li >> "second").root
    f.root.insert_before(second, third)
    assert str(f) == "<ul><li>first</li><li>second</li><li>third</li></ul>"


def test_insert_before_invalid_reference():
    f = shift(ul() >> (li >> "first",))
    orphan = shift(li >> "orphan").root
    new = shift(li >> "new").root
    with pytest.raises(ValueError, match="not a child"):
        f.root.insert_before(new, orphan)


def test_replace_child():
    f = shift(div() >> (p >> "old",))
    old = f.root.first_child
    assert old is not None
    new = shift(span >> "new").root
    returned = f.root.replace_child(new, old)
    assert returned is old
    assert old.parent_node is None
    assert str(f) == "<div><span>new</span></div>"


def test_replace_child_not_found():
    f = shift(div() >> (p >> "child",))
    orphan = p()
    new = span()
    with pytest.raises(ValueError, match="not a child"):
        f.root.replace_child(new, orphan)


def test_contains():
    f = shift(div() >> p >> span >> "deep")
    root = f.root
    first = root.first_child
    assert first is not None
    deep_span = first.first_child
    assert deep_span is not None
    assert root.contains(deep_span) is True
    assert root.contains(root) is True

    orphan = h1()
    assert root.contains(orphan) is False


def test_mutation_preserves_siblings():
    parent = ul()
    a = shift(li >> "a").root
    b = shift(li >> "b").root
    c = shift(li >> "c").root
    parent.append_child(a)
    parent.append_child(b)
    parent.append_child(c)
    b.remove()
    assert a.next_sibling is c
    assert c.previous_sibling is a
