from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class LitestarWebSocket(Protocol):
    """Protocol matching the Litestar WebSocket interface."""

    accept: Callable[[], Awaitable[None]]
    close: Callable[[], Awaitable[None]]
    send_data: Callable[[str], Awaitable[None]]
    receive_data: Callable[[], Awaitable[str]]


@asynccontextmanager
async def websocket(ws: LitestarWebSocket) -> AsyncIterator[Connection]:
    """Wrap a Litestar WebSocket as a Connection.

    Handles accept/close lifecycle automatically.
    """
    await ws.accept()
    try:
        yield Connection(
            send_text=ws.send_data,
            receive_text=ws.receive_data,
            close=ws.close,
        )
    finally:
        await ws.close()
