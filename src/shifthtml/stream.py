from __future__ import annotations

from .rendering import render

__all__ = ("sse",)


def sse(node: object, *, event: str | None = None, id: str | None = None) -> str:
    """Format a renderable node as a Server-Sent Event string.

    Returns the complete SSE event including trailing blank line.
    """
    html = render(node)
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
