import pytest

from shifthtml import IterationNode, args, div, li, ul

pytestmark = pytest.mark.anyio


async def test_renders_per_item():
    tree = div() >> args.items.map(lambda x: li() >> x)
    assert await tree.render(args={"items": ["a", "b", "c"]}) == "<div><li>a</li><li>b</li><li>c</li></div>"


async def test_empty_iterable():
    tree = div() >> args.items.map(lambda x: li() >> x)
    assert await tree.render(args={"items": []}) == "<div></div>"


async def test_inside_element():
    tree = ul() >> args.items.map(lambda x: li() >> x)
    assert await tree.render(args={"items": ["a", "b"]}) == "<ul><li>a</li><li>b</li></ul>"


def test_rshift_raises():
    node = args.items.map(lambda x: x)
    with pytest.raises(TypeError, match="does not support >>"):
        node >> "more"


def test_append_child_raises():
    node = args.items.map(lambda x: x)
    with pytest.raises(TypeError, match="does not support children"):
        node.append_child("child")


def test_repr():
    fn = lambda x: x  # noqa: E731
    node = args.items.map(fn)
    assert "IterationNode" in repr(node)
    assert "Var('items')" in repr(node)


def test_iteration_node_replace():
    node = args.items.map(lambda x: li() >> x)
    clone = node.__replace__()
    assert isinstance(clone, IterationNode)
    assert clone is not node
    assert clone.var.name == "items"


async def test_stream():
    tree = ul() >> args.items.map(lambda x: li() >> x)
    chunks = [chunk async for chunk in tree.stream(args={"items": ["a", "b"]})]
    assert "".join(chunks) == "<ul><li>a</li><li>b</li></ul>"
