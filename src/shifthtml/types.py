from collections.abc import Callable, Iterable
from string.templatelib import Template
from typing import TYPE_CHECKING

from .node import Node

if TYPE_CHECKING:
    from .element import Fragment

type NodeAtom = type[Node] | Node | Fragment | str | Template
type NodeListContent = Iterable[NodeAtom | Callable[[], NodeAtom] | None]
type NodeContent = NodeAtom | NodeListContent | Callable[[], NodeAtom | NodeListContent]
