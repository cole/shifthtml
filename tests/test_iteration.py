import pytest

from shifthtml import IterationNode, div, li, slots, ul

pytestmark = pytest.mark.anyio


async def test_renders_per_item():
    tree = div() >> slots.items.map(lambda x: li() >> x)
    assert await tree.render(params={"items": ["a", "b", "c"]}) == "<div><li>a</li><li>b</li><li>c</li></div>"


async def test_empty_iterable():
    tree = div() >> slots.items.map(lambda x: li() >> x)
    assert await tree.render(params={"items": []}) == "<div></div>"


async def test_inside_element():
    tree = ul() >> slots.items.map(lambda x: li() >> x)
    assert await tree.render(params={"items": ["a", "b"]}) == "<ul><li>a</li><li>b</li></ul>"


def test_rshift_raises():
    node = slots.items.map(lambda x: x)
    with pytest.raises(TypeError, match="does not support >>"):
        node >> "more"


def test_append_child_raises():
    node = slots.items.map(lambda x: x)
    with pytest.raises(TypeError, match="does not support children"):
        node.append_child("child")


def test_repr():
    fn = lambda x: x  # noqa: E731
    node = slots.items.map(fn)
    assert "IterationNode" in repr(node)
    assert "Slot('items')" in repr(node)


def test_iteration_node_replace():
    node = slots.items.map(lambda x: li() >> x)
    clone = node.__replace__()
    assert isinstance(clone, IterationNode)
    assert clone is not node
    assert clone.slot.name == "items"


async def test_stream():
    tree = ul() >> slots.items.map(lambda x: li() >> x)
    chunks = [chunk async for chunk in tree.stream(params={"items": ["a", "b"]})]
    assert "".join(chunks) == "<ul><li>a</li><li>b</li></ul>"
