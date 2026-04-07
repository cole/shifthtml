from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class SanicWebSocket(Protocol):
    """Protocol matching the Sanic WebSocket interface."""

    send: Callable[[str], Awaitable[None]]
    recv: Callable[[], Awaitable[str | bytes]]
    close: Callable[[], Awaitable[None]]


@asynccontextmanager
async def websocket(ws: SanicWebSocket) -> AsyncIterator[Connection]:
    """Wrap a Sanic WebSocket as a Connection.

    Sanic accepts the connection before the handler is called.
    """

    async def receive_text() -> str:
        data = await ws.recv()
        if isinstance(data, bytes):
            return data.decode()
        return data

    try:
        yield Connection(
            send_text=ws.send,
            receive_text=receive_text,
            close=ws.close,
        )
    finally:
        await ws.close()
