from collections.abc import Awaitable, Callable, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING

from .tree import TreeNode

if TYPE_CHECKING:
    from .element import Fragment

type NodeAtom = TreeNode | Fragment
type NodeListContent = Iterable[
    NodeAtom
    | str
    | Template
    | Callable[[], NodeAtom | str | Template]
    | Callable[[], Awaitable[NodeAtom | str | Template]]
    | None
]
type NodeContent = (
    NodeAtom
    | str
    | Template
    | NodeListContent
    | Callable[[], NodeAtom | str | Template | NodeListContent]
    | Callable[[], Awaitable[NodeAtom | str | Template | NodeListContent]]
)
