import json

import pytest

from shifthtml import span
from shifthtml.live import replace
from shifthtml.ws.starlette import websocket


class MockWebSocket:
    def __init__(self, incoming: list[str] | None = None):
        self.accepted = False
        self.closed = False
        self.sent: list[str] = []
        self._incoming = list(incoming or [])

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.closed = True

    async def send_text(self, data: str) -> None:
        self.sent.append(data)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise Exception("no more messages")
        return self._incoming.pop(0)


@pytest.mark.anyio
async def test_websocket_accepts_and_closes():
    ws = MockWebSocket()
    async with websocket(ws) as conn:
        assert ws.accepted
        assert conn is not None
    assert ws.closed


@pytest.mark.anyio
async def test_websocket_send_mutation():
    ws = MockWebSocket()
    async with websocket(ws) as conn:
        m = replace("x", span() >> "hi")
        await conn.send(m)
    assert len(ws.sent) == 1
    parsed = json.loads(ws.sent[0])
    assert parsed["action"] == "replace"
    assert parsed["target"] == "x"
    assert parsed["html"] == "<span>hi</span>"


@pytest.mark.anyio
async def test_websocket_receive_messages():
    ws = MockWebSocket(
        incoming=[
            json.dumps({"event": "ping"}),
            json.dumps({"event": "msg", "text": "hi"}),
        ]
    )
    messages = []
    async with websocket(ws) as conn:
        for _ in range(2):
            msg = await conn.__anext__()
            messages.append(msg)
    assert messages[0] == {"event": "ping"}
    assert messages[1] == {"event": "msg", "text": "hi"}
