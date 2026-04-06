import inspect
from collections.abc import Awaitable, Callable, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING, TypeGuard

from .tree import TreeNode

if TYPE_CHECKING:
    from .element import Fragment

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


def is_node_list(obj: NodeContent) -> TypeGuard[Iterable[NodeContent]]:
    return isinstance(obj, tuple | list)


def is_sync_content_fn(obj: NodeContent) -> TypeGuard[Callable[..., NodeContent]]:
    return callable(obj) and not inspect.iscoroutinefunction(obj)


def is_async_content_fn(obj: NodeContent) -> TypeGuard[Callable[..., Awaitable[NodeContent]]]:
    return callable(obj) and inspect.iscoroutinefunction(obj)
