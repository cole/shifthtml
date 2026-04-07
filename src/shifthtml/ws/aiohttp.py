from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class AiohttpWebSocket(Protocol):
    """Protocol matching aiohttp's WebSocketResponse after prepare()."""

    send_str: Callable[[str], Awaitable[None]]
    receive_str: Callable[[], Awaitable[str]]
    close: Callable[[], Awaitable[bool]]


@asynccontextmanager
async def websocket(ws: AiohttpWebSocket) -> AsyncIterator[Connection]:
    """Wrap an aiohttp WebSocketResponse as a Connection.

    The caller must call ``await ws.prepare(request)`` before entering
    this context manager.
    """

    async def close() -> None:
        await ws.close()

    try:
        yield Connection(
            send_text=ws.send_str,
            receive_text=ws.receive_str,
            close=close,
        )
    finally:
        await ws.close()
