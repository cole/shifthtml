from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class QuartWebSocket(Protocol):
    """Protocol matching the Quart Websocket interface."""

    accept: Callable[[], Awaitable[None]]
    send: Callable[[str], Awaitable[None]]
    receive: Callable[[], Awaitable[str]]


@asynccontextmanager
async def websocket(ws: QuartWebSocket) -> AsyncIterator[Connection]:
    """Wrap a Quart Websocket as a Connection.

    Handles accept lifecycle automatically. Quart closes the connection
    when the handler coroutine returns.
    """
    await ws.accept()

    async def noop() -> None:
        pass

    try:
        yield Connection(
            send_text=ws.send,
            receive_text=ws.receive,
            close=noop,
        )
    finally:
        pass
