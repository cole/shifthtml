from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class LitestarWebSocket(Protocol):
    """Protocol matching the Litestar WebSocket interface."""

    async def accept(self) -> None: ...
    async def close(self) -> None: ...
    async def send_data(self, data: str) -> None: ...
    async def receive_data(self) -> str: ...


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
