import json

import pytest

from shifthtml import li, span
from shifthtml.mutations import Mutation, append, replace
from shifthtml.socket import Connection


@pytest.fixture
def message_log():
    return []


@pytest.fixture
def incoming():
    return []


@pytest.fixture
def conn(message_log, incoming):
    async def send_text(text: str) -> None:
        message_log.append(text)

    async def receive_text() -> str:
        if not incoming:
            raise StopAsyncIteration
        return incoming.pop(0)

    async def close() -> None:
        message_log.append("__closed__")

    return Connection(send_text=send_text, receive_text=receive_text, close=close)


@pytest.mark.anyio
async def test_send_mutation(conn, message_log):
    m = await replace("status", span() >> "Online")
    await conn.send(m)
    assert len(message_log) == 1
    parsed = json.loads(message_log[0])
    assert parsed == {"action": "replace", "target": "status", "html": "<span>Online</span>"}


@pytest.mark.anyio
async def test_send_many(conn, message_log):
    m1 = await replace("a", span() >> "1")
    m2 = await append("b", li() >> "2")
    await conn.send_many(m1, m2)
    assert len(message_log) == 1
    parsed = json.loads(message_log[0])
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["action"] == "replace"
    assert parsed[1]["action"] == "append"


@pytest.mark.anyio
async def test_receive_messages(conn, incoming):
    incoming.extend(
        [
            json.dumps({"event": "send_message", "text": "hello"}),
            json.dumps({"event": "typing", "user": "cole"}),
        ]
    )
    messages = []
    async for msg in conn:
        messages.append(msg)
    assert len(messages) == 2
    assert messages[0] == {"event": "send_message", "text": "hello"}
    assert messages[1] == {"event": "typing", "user": "cole"}


@pytest.mark.anyio
async def test_close(conn, message_log):
    await conn.close()
    assert "__closed__" in message_log


@pytest.mark.anyio
async def test_send_remove_mutation(conn, message_log):
    m = Mutation("remove", "old-item")
    await conn.send(m)
    parsed = json.loads(message_log[0])
    assert parsed == {"action": "remove", "target": "old-item"}
    assert "html" not in parsed
