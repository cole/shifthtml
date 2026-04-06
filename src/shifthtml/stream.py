from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Renderable

__all__ = ("sse",)


def sse(node: Renderable, *, event: str | None = None, id: str | None = None) -> str:
    """Format a renderable node as a Server-Sent Event string.

    Returns the complete SSE event including trailing blank line.
    """
    html = node.render()
    parts: list[str] = []
    if event is not None:
        parts.append(f"event: {event}")
    if id is not None:
        parts.append(f"id: {id}")
    for line in html.split("\n"):
        parts.append(f"data: {line}")
    parts.append("")
    parts.append("")
    return "\n".join(parts)
