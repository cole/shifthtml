from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from . import Connection

__all__ = ("websocket",)


class StarletteWebSocket(Protocol):
    """Protocol matching the Starlette/FastAPI WebSocket interface."""

    async def accept(self) -> None: ...
    async def close(self) -> None: ...
    async def send_text(self, data: str) -> None: ...
    async def receive_text(self) -> str: ...


@asynccontextmanager
async def websocket(ws: StarletteWebSocket) -> AsyncIterator[Connection]:
    """Wrap a Starlette/FastAPI WebSocket as a Connection.

    Handles accept/close lifecycle automatically.
    """
    await ws.accept()
    try:
        yield Connection(
            send_text=ws.send_text,
            receive_text=ws.receive_text,
            close=ws.close,
        )
    finally:
        await ws.close()
