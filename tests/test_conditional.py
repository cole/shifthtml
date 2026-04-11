import pytest

from shifthtml import ConditionalNode, args, div, h1, p

pytestmark = pytest.mark.anyio


async def test_truthy_renders_content():
    tree = div() >> (args.show & (p() >> "yes"),)
    assert await tree.render(args={"show": True}) == "<div><p>yes</p></div>"


async def test_falsy_renders_nothing():
    tree = div() >> (args.show & (p() >> "yes"),)
    assert await tree.render(args={"show": False}) == "<div></div>"


async def test_with_else_truthy():
    cond = (args.show & (p() >> "yes")) | (p() >> "no")
    tree = div() >> (cond,)
    assert await tree.render(args={"show": True}) == "<div><p>yes</p></div>"


async def test_with_else_falsy():
    cond = (args.show & (p() >> "yes")) | (p() >> "no")
    tree = div() >> (cond,)
    assert await tree.render(args={"show": False}) == "<div><p>no</p></div>"


async def test_callable_only_invoked_when_branch_taken():
    calls: list[int] = []

    def make_content():
        calls.append(1)
        return p() >> "lazy"

    tree = div() >> (args.show & make_content,)

    await tree.render(args={"show": False})
    assert calls == []

    await tree.render(args={"show": True})
    assert calls == [1]


async def test_inside_element_with_siblings():
    tree = div() >> (h1() >> "Title", args.show & (p() >> "visible"))
    assert await tree.render(args={"show": True}) == "<div><h1>Title</h1><p>visible</p></div>"
    assert await tree.render(args={"show": False}) == "<div><h1>Title</h1></div>"


async def test_nested_conditionals():
    cond = args.a & (args.b & (p() >> "both"))
    tree = div() >> (cond,)
    assert await tree.render(args={"a": True, "b": True}) == "<div><p>both</p></div>"
    assert await tree.render(args={"a": True, "b": False}) == "<div></div>"
    assert await tree.render(args={"a": False, "b": True}) == "<div></div>"


def test_double_else_raises():
    cond = (args.x & "yes") | "no"
    with pytest.raises(TypeError, match="already has an else branch"):
        cond | "maybe"


def test_rshift_raises():
    cond = args.x & "yes"
    with pytest.raises(TypeError, match="does not support >>"):
        cond >> "more"


def test_append_child_raises():
    cond = args.x & "yes"
    with pytest.raises(TypeError, match="does not support children"):
        cond.append_child("child")


def test_repr_without_else():
    cond = args.x & "yes"
    assert repr(cond) == "ConditionalNode(Var('x'), 'yes')"


def test_repr_with_else():
    cond = (args.x & "yes") | "no"
    assert repr(cond) == "ConditionalNode(Var('x'), 'yes', 'no')"


def test_or_is_immutable():
    cond = args.x & "yes"
    cond_else = cond | "no"
    assert cond.if_false is None
    assert cond_else.if_false == "no"
    assert isinstance(cond_else, ConditionalNode)


async def test_stream():
    cond = (args.show & (p() >> "yes")) | (p() >> "no")
    tree = div() >> (cond,)

    chunks = [chunk async for chunk in tree.stream(args={"show": True})]
    assert "".join(chunks) == "<div><p>yes</p></div>"

    chunks = [chunk async for chunk in tree.stream(args={"show": False})]
    assert "".join(chunks) == "<div><p>no</p></div>"


def test_conditional_node_replace():
    cond = args.show & (p() >> "yes")
    clone = cond.__replace__()
    assert isinstance(clone, ConditionalNode)
    assert clone is not cond
    assert clone.var.name == "show"


async def test_async_callable_in_branch():
    async def fetch():
        return p() >> "fetched"

    tree = div() >> (args.show & fetch,)

    chunks = [chunk async for chunk in tree.stream(args={"show": True})]
    assert "".join(chunks) == "<div><p>fetched</p></div>"
