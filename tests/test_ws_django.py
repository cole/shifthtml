import json

import pytest

from shifthtml import li, span
from shifthtml.live import append, replace
from shifthtml.ws.django import websocket


class MockDjangoConsumer:
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.sent: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if text_data is not None:
            self.sent.append(text_data)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.anyio
async def test_websocket_accepts():
    consumer = MockDjangoConsumer()
    conn, bridge = await websocket(consumer)
    assert consumer.accepted
    assert conn is not None
    assert bridge is not None


@pytest.mark.anyio
async def test_send_mutation():
    consumer = MockDjangoConsumer()
    conn, _bridge = await websocket(consumer)
    await conn.send(replace("x", span() >> "hi"))
    parsed = json.loads(consumer.sent[0])
    assert parsed == {"action": "replace", "target": "x", "html": "<span>hi</span>"}


@pytest.mark.anyio
async def test_send_many():
    consumer = MockDjangoConsumer()
    conn, _bridge = await websocket(consumer)
    await conn.send_many(
        replace("a", span() >> "1"),
        append("b", li() >> "2"),
    )
    parsed = json.loads(consumer.sent[0])
    assert isinstance(parsed, list)
    assert len(parsed) == 2


@pytest.mark.anyio
async def test_receive_via_bridge():
    consumer = MockDjangoConsumer()
    conn, bridge = await websocket(consumer)
    await bridge.feed(json.dumps({"event": "msg", "text": "hello"}))
    await bridge.feed(json.dumps({"event": "typing"}))
    msg1 = await conn.__anext__()
    msg2 = await conn.__anext__()
    assert msg1 == {"event": "msg", "text": "hello"}
    assert msg2 == {"event": "typing"}


@pytest.mark.anyio
async def test_feed_disconnect_stops_iteration():
    consumer = MockDjangoConsumer()
    conn, bridge = await websocket(consumer)
    await bridge.feed(json.dumps({"event": "ping"}))
    await bridge.feed_disconnect()
    messages = []
    async for msg in conn:
        messages.append(msg)
    assert len(messages) == 1
    assert messages[0] == {"event": "ping"}


@pytest.mark.anyio
async def test_close():
    consumer = MockDjangoConsumer()
    conn, _bridge = await websocket(consumer)
    await conn.close()
    assert consumer.closed
