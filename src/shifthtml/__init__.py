from .tags import h1, ul, li, img
from .node import Node, NodeListType

__all__ = (
    'h1',
    'ul',
    'button',
    'li',
    'img',
    'shift',
)


def shift(html: Node | NodeListType) -> str:
    parts = []
    if isinstance(html, Node):
        parts.extend(html.render())
    else:
        for node in html:
            parts.extend(node.render())
        

    return "".join(parts)
