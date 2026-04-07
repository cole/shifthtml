from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from . import Connection

__all__ = ("Bridge", "websocket")


class DjangoConsumer(Protocol):
    """Protocol matching Django Channels AsyncWebsocketConsumer."""

    accept: Callable[[], Awaitable[None]]
    close: Callable[[], Awaitable[None]]

    async def send(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None: ...


class Bridge:
    """Queues messages from Django Channels' receive() callback for async iteration.

    Wire this into your consumer::

        async def connect(self):
            self.conn, self.bridge = await websocket(self)

        async def receive(self, text_data=None, bytes_data=None):
            if text_data is not None:
                await self.bridge.feed(text_data)

        async def disconnect(self, close_code):
            await self.bridge.feed_disconnect()
    """

    __slots__ = ("_queue",)

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def feed(self, text: str) -> None:
        """Push a received text message into the queue."""
        await self._queue.put(text)

    async def feed_disconnect(self) -> None:
        """Signal that the connection has closed."""
        await self._queue.put(None)

    async def _receive_text(self) -> str:
        data = await self._queue.get()
        if data is None:
            raise StopAsyncIteration
        return data


async def websocket(consumer: DjangoConsumer) -> tuple[Connection, Bridge]:
    """Create a Connection from a Django Channels consumer.

    Returns ``(connection, bridge)``. Wire ``bridge.feed()`` to the
    consumer's ``receive()`` and ``bridge.feed_disconnect()`` to
    ``disconnect()`` so that ``async for msg in connection`` works.
    """
    await consumer.accept()
    bridge = Bridge()

    async def send_text(data: str) -> None:
        await consumer.send(text_data=data)

    async def close() -> None:
        await consumer.close()

    conn = Connection(
        send_text=send_text,
        receive_text=bridge._receive_text,
        close=close,
    )
    return conn, bridge
