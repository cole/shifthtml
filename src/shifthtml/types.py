import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable

if TYPE_CHECKING:
    from .element import Fragment
    from .plugin import RenderContext
    from .tree import TreeNode

_MISSING: object = object()


@runtime_checkable
class Streamable(Protocol):
    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]: ...
    def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]: ...


type NodeContent = (
    TreeNode
    | Fragment
    | str
    | Template
    | bool
    | Iterable[NodeContent]
    | Callable[[], NodeContent | Awaitable[NodeContent]]
    | None
)


def is_node_list(obj: object) -> TypeGuard[Iterable[NodeContent]]:
    return isinstance(obj, tuple | list)


def is_sync_content_fn(obj: object) -> TypeGuard[Callable[..., NodeContent]]:
    return callable(obj) and not inspect.iscoroutinefunction(obj)


def is_async_content_fn(obj: object) -> TypeGuard[Callable[..., Awaitable[NodeContent]]]:
    return callable(obj) and inspect.iscoroutinefunction(obj)
