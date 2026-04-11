from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator

from .errors import RenderLimitExceeded
from .rendering import RenderContext, arender_result
from .tree import Node

_LAZY_TYPE_ERROR = (
    "Lazy nodes require async rendering. Use `await node.render()` or `async for chunk in node.stream()`."
)


class Lazy(Node):
    """Wraps a zero-arg callable, resolved during rendering.

    Handles both sync and async callables. All Lazy nodes require async
    rendering — _collect and chunks raise TypeError. Use render() or stream().
    """

    __slots__ = ("fn", "_is_async")

    fn: Callable[..., object]
    _is_async: bool

    def __init__(self, fn: Callable[..., object], /):
        super().__init__()
        self.fn = fn
        self._is_async = inspect.iscoroutinefunction(fn)

    def __repr__(self) -> str:
        return f"Lazy({self.fn!r})"

    def __replace__(self, **changes: object) -> Lazy:
        return type(self)(self.fn)

    def _collect(self, buf: list[str]) -> None:
        raise TypeError(_LAZY_TYPE_ERROR)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError(_LAZY_TYPE_ERROR)
        yield  # unreachable, but makes this a generator function

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        result = self.fn()
        if isinstance(result, Awaitable):
            result = await result
        async for chunk in arender_result(result, ctx):
            yield chunk
        if ctx is not None:
            ctx._depth -= 1
