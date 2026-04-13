import pytest

from shifthtml import ConditionalNode, div, h1, p, slots

pytestmark = pytest.mark.anyio


async def test_truthy_renders_content():
    tree = div() >> (slots.show.then(p() >> "yes"),)
    assert await tree.render(params={"show": True}) == "<div><p>yes</p></div>"


async def test_falsy_renders_nothing():
    tree = div() >> (slots.show.then(p() >> "yes"),)
    assert await tree.render(params={"show": False}) == "<div></div>"


async def test_with_else_truthy():
    cond = slots.show.then(p() >> "yes").otherwise(p() >> "no")
    tree = div() >> (cond,)
    assert await tree.render(params={"show": True}) == "<div><p>yes</p></div>"


async def test_with_else_falsy():
    cond = slots.show.then(p() >> "yes").otherwise(p() >> "no")
    tree = div() >> (cond,)
    assert await tree.render(params={"show": False}) == "<div><p>no</p></div>"


async def test_callable_only_invoked_when_branch_taken():
    calls: list[int] = []

    def make_content():
        calls.append(1)
        return p() >> "lazy"

    tree = div() >> (slots.show.then(make_content),)

    await tree.render(params={"show": False})
    assert calls == []

    await tree.render(params={"show": True})
    assert calls == [1]


async def test_inside_element_with_siblings():
    tree = div() >> (h1() >> "Title", slots.show.then(p() >> "visible"))
    assert await tree.render(params={"show": True}) == "<div><h1>Title</h1><p>visible</p></div>"
    assert await tree.render(params={"show": False}) == "<div><h1>Title</h1></div>"


async def test_nested_conditionals():
    cond = slots.a.then(slots.b.then(p() >> "both"))
    tree = div() >> (cond,)
    assert await tree.render(params={"a": True, "b": True}) == "<div><p>both</p></div>"
    assert await tree.render(params={"a": True, "b": False}) == "<div></div>"
    assert await tree.render(params={"a": False, "b": True}) == "<div></div>"


def test_double_else_raises():
    cond = slots.x.then("yes").otherwise("no")
    with pytest.raises(TypeError, match="already has an else branch"):
        cond.otherwise("maybe")


def test_rshift_raises():
    cond = slots.x.then("yes")
    with pytest.raises(TypeError, match="does not support >>"):
        cond >> "more"


def test_append_child_raises():
    cond = slots.x.then("yes")
    with pytest.raises(TypeError, match="does not support children"):
        cond.append_child("child")


def test_repr_without_else():
    cond = slots.x.then("yes")
    assert repr(cond) == "ConditionalNode(Slot('x'), 'yes')"


def test_repr_with_else():
    cond = slots.x.then("yes").otherwise("no")
    assert repr(cond) == "ConditionalNode(Slot('x'), 'yes', 'no')"


def test_otherwise_is_immutable():
    cond = slots.x.then("yes")
    cond_else = cond.otherwise("no")
    assert cond.if_false is None
    assert cond_else.if_false == "no"
    assert isinstance(cond_else, ConditionalNode)


async def test_stream():
    cond = slots.show.then(p() >> "yes").otherwise(p() >> "no")
    tree = div() >> (cond,)

    chunks = [chunk async for chunk in tree.stream(params={"show": True})]
    assert "".join(chunks) == "<div><p>yes</p></div>"

    chunks = [chunk async for chunk in tree.stream(params={"show": False})]
    assert "".join(chunks) == "<div><p>no</p></div>"


def test_conditional_node_replace():
    cond = slots.show.then(p() >> "yes")
    clone = cond.__replace__()
    assert isinstance(clone, ConditionalNode)
    assert clone is not cond
    assert clone.slot.name == "show"


async def test_async_callable_in_branch():
    async def fetch():
        return p() >> "fetched"

    tree = div() >> (slots.show.then(fetch),)

    chunks = [chunk async for chunk in tree.stream(params={"show": True})]
    assert "".join(chunks) == "<div><p>fetched</p></div>"
