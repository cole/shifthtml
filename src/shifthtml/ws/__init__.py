from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..live import Mutation

type SendText = Callable[[str], Awaitable[None]]
type ReceiveText = Callable[[], Awaitable[str]]
type Close = Callable[[], Awaitable[None]]

__all__ = ("Connection",)


class Connection:
    """A single WebSocket connection.

    Framework adapters wrap their native WebSocket into this class.
    Provides send/receive with JSON serialization.
    """

    __slots__ = ("_send_text", "_receive_text", "_close")

    _send_text: SendText
    _receive_text: ReceiveText
    _close: Close

    def __init__(
        self,
        send_text: SendText,
        receive_text: ReceiveText,
        close: Close,
    ) -> None:
        self._send_text = send_text
        self._receive_text = receive_text
        self._close = close

    async def send(self, mutation: Mutation) -> None:
        """Send a mutation to this client."""
        await self._send_text(mutation.json())

    async def send_many(self, *mutations: Mutation) -> None:
        """Send multiple mutations as a JSON array."""
        await self._send_text("[" + ",".join(m.json() for m in mutations) + "]")

    def __aiter__(self) -> Connection:
        return self

    async def __anext__(self) -> dict[str, object]:
        """Yield the next message from the client as a parsed dict."""
        text = await self._receive_text()
        return json.loads(text)

    async def close(self) -> None:
        """Close the underlying WebSocket."""
        await self._close()
