from collections.abc import Callable, Iterable

from .compat import Template
from .protocol import Node, NodeTree

type NodeClassContent = type[Node] | Node | NodeTree
type NodeTextContent = str | Template
type NodeListContent = Iterable[NodeClassContent | NodeTextContent]
type NodeCallableContent = Callable[[], NodeClassContent | NodeTextContent | NodeListContent]
type NodeContent = NodeClassContent | NodeTextContent | NodeListContent | NodeCallableContent
