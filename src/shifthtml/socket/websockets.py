from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class WebSocketsConnection(Protocol):
    """Protocol matching the websockets library ServerConnection."""

    async def send(self, data: str) -> None: ...
    async def recv(self) -> str | bytes: ...
    async def close(self) -> None: ...


@asynccontextmanager
async def websocket(ws: WebSocketsConnection) -> AsyncIterator[Connection]:
    """Wrap a websockets library connection as a Connection.

    The websockets library accepts connections before the handler is called.
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
