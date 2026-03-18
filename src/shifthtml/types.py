from collections.abc import Callable, Iterable
from string.templatelib import Template

from .node import Node

type NodeClassContent = type[Node] | Node
type NodeTextContent = str | Template
type NodeListContent = Iterable[NodeClassContent | NodeTextContent]
type NodeCallableContent = Callable[[], NodeClassContent | NodeTextContent | NodeListContent]
type NodeContent = NodeClassContent | NodeTextContent | NodeListContent | NodeCallableContent
