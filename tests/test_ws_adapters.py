import json

import pytest

from shifthtml import span
from shifthtml.live import replace

# -- shared helpers --


class BaseMockWS:
    def __init__(self, incoming: list[str] | None = None):
        self.closed = False
        self.sent: list[str] = []
        self._incoming = list(incoming or [])


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
    from shifthtml.ws.aiohttp import websocket

    ws = MockAiohttpWS()
    async with websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_aiohttp_receive():
    from shifthtml.ws.aiohttp import websocket

    ws = MockAiohttpWS(incoming=[json.dumps({"event": "ping"})])
    async with websocket(ws) as conn:
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
    from shifthtml.ws.quart import websocket

    ws = MockQuartWS()
    async with websocket(ws) as conn:
        assert ws.accepted
        await conn.send(replace("x", span() >> "hi"))
    assert json.loads(ws.sent[0])["target"] == "x"


@pytest.mark.anyio
async def test_quart_receive():
    from shifthtml.ws.quart import websocket

    ws = MockQuartWS(incoming=[json.dumps({"event": "msg", "text": "yo"})])
    async with websocket(ws) as conn:
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
    from shifthtml.ws.sanic import websocket

    ws = MockSanicWS()
    async with websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["html"] == "<span>hi</span>"


@pytest.mark.anyio
async def test_sanic_receive_text():
    from shifthtml.ws.sanic import websocket

    ws = MockSanicWS(incoming=[json.dumps({"event": "ping"})])
    async with websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


@pytest.mark.anyio
async def test_sanic_receive_bytes():
    from shifthtml.ws.sanic import websocket

    ws = MockSanicWS(incoming=[json.dumps({"event": "ping"}).encode()])
    async with websocket(ws) as conn:
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
    from shifthtml.ws.litestar import websocket

    ws = MockLitestarWS()
    async with websocket(ws) as conn:
        assert ws.accepted
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_litestar_receive():
    from shifthtml.ws.litestar import websocket

    ws = MockLitestarWS(incoming=[json.dumps({"event": "hello"})])
    async with websocket(ws) as conn:
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
    from shifthtml.ws.websockets import websocket

    ws = MockWebSocketsConn()
    async with websocket(ws) as conn:
        await conn.send(replace("x", span() >> "hi"))
    assert ws.closed
    assert json.loads(ws.sent[0])["action"] == "replace"


@pytest.mark.anyio
async def test_websockets_receive_text():
    from shifthtml.ws.websockets import websocket

    ws = MockWebSocketsConn(incoming=[json.dumps({"event": "ping"})])
    async with websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}


@pytest.mark.anyio
async def test_websockets_receive_bytes():
    from shifthtml.ws.websockets import websocket

    ws = MockWebSocketsConn(incoming=[json.dumps({"event": "ping"}).encode()])
    async with websocket(ws) as conn:
        msg = await conn.__anext__()
    assert msg == {"event": "ping"}
