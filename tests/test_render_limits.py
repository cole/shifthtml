import pytest

from shifthtml import Lazy, RenderLimitExceeded, div, li, p, ul
from shifthtml.tree import ContainerNode, _flatten_into

pytestmark = pytest.mark.anyio


def _recursive_lazy(depth: int = 0):
    return Lazy(lambda d=depth: _recursive_lazy(d + 1))


async def test_max_depth_lazy_recursion():
    tag = div() >> _recursive_lazy()
    with pytest.raises(RenderLimitExceeded, match="max render depth"):
        await tag.render(max_depth=5)


async def test_max_depth_default():
    tag = div() >> (ul() >> (li() >> (p() >> "deep")))
    assert "deep" in await tag.render()


async def test_max_nodes_exceeded():
    tag = div() >> tuple(p() >> f"item {i}" for i in range(20))
    with pytest.raises(RenderLimitExceeded, match="max node count"):
        await tag.render(max_nodes=5)


async def test_max_nodes_unlimited():
    tag = div() >> tuple(p() >> f"item {i}" for i in range(200))
    result = await tag.render()
    assert "item 199" in result


def test_flatten_into_depth_limit():
    nested: object = ("leaf",)
    for _ in range(150):
        nested = (nested,)
    node = ContainerNode()
    with pytest.raises(RenderLimitExceeded, match="max nesting depth"):
        _flatten_into(node, (nested,))


async def test_depth_resets_after_lazy():
    call_count = 0

    def counting_fn():
        nonlocal call_count
        call_count += 1
        return f"call {call_count}"

    tag = div() >> (Lazy(counting_fn), Lazy(counting_fn), Lazy(counting_fn))
    result = await tag.render(max_depth=2)
    assert "call 1" in result
    assert "call 3" in result


async def test_limits_on_render_path():
    tag = div() >> _recursive_lazy()
    with pytest.raises(RenderLimitExceeded, match="max render depth"):
        await tag.render(max_depth=3)


async def test_limits_on_stream_path():
    tag = div() >> _recursive_lazy()
    with pytest.raises(RenderLimitExceeded, match="max render depth"):
        async for _ in tag.stream(max_depth=3):
            pass


async def test_limits_on_async_path():
    tag = div() >> _recursive_lazy()
    with pytest.raises(RenderLimitExceeded, match="max render depth"):
        chunks = []
        async for chunk in tag.stream(max_depth=3):
            chunks.append(chunk)


async def test_normal_tree_within_limits():
    tag = div() >> (
        ul() >> tuple(li() >> f"item {i}" for i in range(50)),
        p() >> "footer",
    )
    result = await tag.render()
    assert "item 49" in result
    assert "footer" in result


async def test_max_nodes_on_stream_path():
    tag = div() >> tuple(p() >> f"item {i}" for i in range(20))
    with pytest.raises(RenderLimitExceeded, match="max node count"):
        async for _ in tag.stream(max_nodes=5):
            pass
