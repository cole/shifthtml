from collections.abc import Sequence
from string.templatelib import Template

from .node import Node, ElementNode


class Element:
    tag: str

    def __init__(self, tag: str):
        self.tag = tag

    def __call__(self, *args, **kwds) -> ElementNode:
        return ElementNode(self.tag, kwds, args or None)

    def __rshift__(self, other: Sequence[Node] | Node | str | Template) -> ElementNode:
        instance = self()
        return instance >> other
