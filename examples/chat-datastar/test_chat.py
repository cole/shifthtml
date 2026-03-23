from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from components import Message, chat_input, message_bubble, message_list
from freezegun import freeze_time
from pages import chat_page, landing_page

from shifthtml import shift

FROZEN = "2025-06-15 12:00:00"
TS = datetime(2025, 6, 15, 12, 0, 0)


def render(node) -> str:
    return str(shift(node))


async def arender(node) -> str:
    return "".join([chunk async for chunk in shift(node).arender()])


def make_message(username: str = "alice", text: str = "hello") -> Message:
    return Message(username=username, text=text, timestamp=TS)


def test_message_bubble(snapshot):
    assert render(message_bubble(make_message("alice", "hello world"))) == snapshot


def test_message_list_empty(snapshot):
    assert render(message_list([])) == snapshot


def test_message_list_with_messages(snapshot):
    msgs = [make_message("alice", "hi"), make_message("bob", "hey")]
    assert render(message_list(msgs)) == snapshot


def test_chat_input(snapshot):
    assert render(chat_input()) == snapshot


def test_landing_page(snapshot):
    assert render(landing_page()) == snapshot


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
