import json

import pytest

from shifthtml import span
from shifthtml.mutations import replace
from shifthtml.socket.aiohttp import websocket as aiohttp_websocket
from shifthtml.socket.litestar import websocket as litestar_websocket
from shifthtml.socket.quart import websocket as quart_websocket
from shifthtml.socket.sanic import websocket as sanic_websocket
from shifthtml.socket.starlette import websocket as starlette_websocket
from shifthtml.socket.websockets import websocket as websockets_websocket

# -- shared helpers --


class BaseMockWS:
    def __init__(self, incoming: list[str] | None = None):
        self.closed = False
        self.sent: list[str] = []
        self._incoming = list(incoming or [])


# -- starlette --


class MockStarletteWS(BaseMockWS):
    def __init__(self, incoming: list[str] | None = None):
        super().__init__(incoming)
        self.accepted = False

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
async def test_starlette_accepts_and_closes():
    ws = MockStarletteWS()
    async with starlette_websocket(ws) as conn:
        assert ws.accepted
        assert conn is not None
    assert ws.closed


@pytest.mark.anyio
async def test_starlette_send():
    ws = MockStarletteWS()
    async with starlette_websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    parsed = json.loads(ws.sent[0])
    assert parsed == {"action": "replace", "target": "x", "html": "<span>hi</span>"}


@pytest.mark.anyio
async def test_starlette_receive():
    ws = MockStarletteWS(
        incoming=[
            json.dumps({"event": "ping"}),
            json.dumps({"event": "msg", "text": "hi"}),
        ]
    )
    messages = []
    async with starlette_websocket(ws) as conn:
        for _ in range(2):
            msg = await conn.__anext__()
            messages.append(msg)
    assert messages[0] == {"event": "ping"}
    assert messages[1] == {"event": "msg", "text": "hi"}


# -- aiohttp --


class MockAiohttpWS(BaseMockWS):
    async def send_str(self, data: str) -> None:
        self.sent.append(data)

    async def receive_str(self) -> str:
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)

    async def close(self) -> bool:
        self.closed = True
        return True


@pytest.mark.anyio
async def test_aiohttp_send_and_close():
    ws = MockAiohttpWS()
    async with aiohttp_websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_aiohttp_receive():
    ws = MockAiohttpWS(incoming=[json.dumps({"event": "ping"})])
    async with aiohttp_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


# -- quart --


class MockQuartWS(BaseMockWS):
    def __init__(self, incoming: list[str] | None = None):
        super().__init__(incoming)
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def receive(self) -> str:
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)


@pytest.mark.anyio
async def test_quart_accepts_and_sends():
    ws = MockQuartWS()
    async with quart_websocket(ws) as conn:
        assert ws.accepted
        await conn.send(replace("x", span() >> "hi"))
    assert json.loads(ws.sent[0])["target"] == "x"


@pytest.mark.anyio
async def test_quart_receive():
    ws = MockQuartWS(incoming=[json.dumps({"event": "msg", "text": "yo"})])
    async with quart_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "msg", "text": "yo"}


# -- sanic --


class MockSanicWS(BaseMockWS):
    def __init__(self, incoming: list[str | bytes] | None = None):
        super().__init__()
        self._incoming_raw: list[str | bytes] = list(incoming or [])

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def recv(self) -> str | bytes:
        if not self._incoming_raw:
            raise StopAsyncIteration
        return self._incoming_raw.pop(0)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.anyio
async def test_sanic_send_and_close():
    ws = MockSanicWS()
    async with sanic_websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["html"] == "<span>hi</span>"


@pytest.mark.anyio
async def test_sanic_receive_text():
    ws = MockSanicWS(incoming=[json.dumps({"event": "ping"})])
    async with sanic_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


@pytest.mark.anyio
async def test_sanic_receive_bytes():
    ws = MockSanicWS(incoming=[json.dumps({"event": "ping"}).encode()])
    async with sanic_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


# -- litestar --


class MockLitestarWS(BaseMockWS):
    def __init__(self, incoming: list[str] | None = None):
        super().__init__(incoming)
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def close(self) -> None:
        self.closed = True

    async def send_data(self, data: str) -> None:
        self.sent.append(data)

    async def receive_data(self) -> str:
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)


@pytest.mark.anyio
async def test_litestar_accepts_and_closes():
    ws = MockLitestarWS()
    async with litestar_websocket(ws) as conn:
        assert ws.accepted
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_litestar_receive():
    ws = MockLitestarWS(incoming=[json.dumps({"event": "hello"})])
    async with litestar_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "hello"}


# -- websockets --


class MockWebSocketsConn(BaseMockWS):
    def __init__(self, incoming: list[str | bytes] | None = None):
        super().__init__()
        self._incoming_raw: list[str | bytes] = list(incoming or [])

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def recv(self) -> str | bytes:
        if not self._incoming_raw:
            raise StopAsyncIteration
        return self._incoming_raw.pop(0)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.anyio
async def test_websockets_send_and_close():
    ws = MockWebSocketsConn()
    async with websockets_websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_websockets_receive_text():
    ws = MockWebSocketsConn(incoming=[json.dumps({"event": "ping"})])
    async with websockets_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


@pytest.mark.anyio
async def test_websockets_receive_bytes():
    ws = MockWebSocketsConn(incoming=[json.dumps({"event": "ping"}).encode()])
    async with websockets_websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}
