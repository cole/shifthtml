from collections.abc import Awaitable, Callable, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING

from .tree import TreeNode as Node

if TYPE_CHECKING:
    from .element import Fragment

type NodeAtom = type[Node] | Node | Fragment | str | Template
type NodeListContent = Iterable[NodeAtom | Callable[[], NodeAtom] | Callable[[], Awaitable[NodeAtom]] | None]
type NodeContent = (
    NodeAtom
    | NodeListContent
    | Callable[[], NodeAtom | NodeListContent]
    | Callable[[], Awaitable[NodeAtom | NodeListContent]]
)
