import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable

if TYPE_CHECKING:
    from .element import Fragment
    from .rendering import RenderContext
    from .tree import Node

_MISSING: object = object()


@runtime_checkable
class Renderable(Protocol):
    """Protocol for objects that can render to HTML.

    Public API: render, stream, astream — used by application code.
    Internal API: _chunks, _achunks — used by the rendering engine
    to thread RenderContext through nested trees.
    """

    def render(self, *, args: dict[str, object] | None = None) -> str: ...
    def stream(self, *, args: dict[str, object] | None = None) -> Generator[str]: ...
    def astream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]: ...
    def _collect(self, buf: list[str]) -> None: ...
    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]: ...
    def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]: ...

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        if cls is Renderable:
            return hasattr(other, "_collect")
        return NotImplemented  # type: ignore[return-value]


type NodeContent = (
    Node
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


def is_content_fn(obj: object) -> TypeGuard[Callable[..., object]]:
    return callable(obj)


def is_sync_content_fn(obj: object) -> TypeGuard[Callable[..., NodeContent]]:
    return callable(obj) and not inspect.iscoroutinefunction(obj)


def is_async_content_fn(obj: object) -> TypeGuard[Callable[..., Awaitable[NodeContent]]]:
    return callable(obj) and inspect.iscoroutinefunction(obj)
