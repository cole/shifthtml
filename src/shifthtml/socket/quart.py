from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class QuartWebSocket(Protocol):
    """Protocol matching the Quart Websocket interface."""

    async def accept(self) -> None: ...
    async def send(self, data: str) -> None: ...
    async def receive(self) -> str: ...


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
