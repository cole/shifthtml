from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from components import Message, chat_input, message_bubble, message_list
from freezegun import freeze_time
from pages import chat_page, landing_page

FROZEN = "2025-06-15 12:00:00"
TS = datetime(2025, 6, 15, 12, 0, 0)


async def arender(node) -> str:
    return "".join([chunk async for chunk in node.astream()])


def make_message(username: str = "alice", text: str = "hello") -> Message:
    return Message(username=username, text=text, timestamp=TS)


def test_message_bubble(snapshot):
    assert message_bubble(make_message("alice", "hello world")).render() == snapshot


def test_message_list_empty(snapshot):
    assert message_list([]).render() == snapshot


def test_message_list_with_messages(snapshot):
    msgs = [make_message("alice", "hi"), make_message("bob", "hey")]
    assert message_list(msgs).render() == snapshot


def test_chat_input(snapshot):
    assert chat_input().render() == snapshot


def test_landing_page(snapshot):
    assert landing_page().render() == snapshot


@pytest.mark.asyncio
@freeze_time(FROZEN)
async def test_chat_page(snapshot):
    msgs = [make_message("alice", "hello")]
    with patch("pages.asyncio.sleep", new_callable=AsyncMock):
        assert await arender(chat_page(msgs, "bob")) == snapshot


@pytest.mark.asyncio
@freeze_time(FROZEN)
async def test_chat_page_empty(snapshot):
    with patch("pages.asyncio.sleep", new_callable=AsyncMock):
        assert await arender(chat_page([], "newuser")) == snapshot
