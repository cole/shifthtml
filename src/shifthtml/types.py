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

    Public API: render (async), stream (async generator) — used by application code.
    Chunk API: chunks (sync generator), achunks (async generator) — used by the
    rendering engine to thread RenderContext through nested trees.
    """

    async def render(self, *, args: dict[str, object] | None = None) -> str: ...
    async def stream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]: ...
    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]: ...
    def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]: ...


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
