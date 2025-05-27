from collections.abc import Sequence

from .tags import h1
from .node import Node

__all__ = (
    'h1',
    'shift'
)


def shift(html: Node | Sequence[Node]) -> str:
    if isinstance(html, Node):
        return html.render()

    return "".join([
        node.render() for node in html
    ])
