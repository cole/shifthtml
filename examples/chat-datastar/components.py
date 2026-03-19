from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from datastar_py import attribute_generator as data

from shifthtml import (
    body,
    button,
    div,
    form,
    h1,
    head,
    html,
    iframe,
    input_,
    link,
    meta,
    script,
    span,
    style,
    title,
)

DATASTAR_CDN = "https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js"

LANDING_CSS = """\
html, body { height: 100%; margin: 0; }
body { display: flex; gap: 2px; background: oklch(0.15 0.02 260); }
.chat-frame { flex: 1; border: none; height: 100%; }
"""


@dataclass
class Message:
    username: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)


def landing_page() -> html:
    page_head = head >> (
        meta({"charset": "UTF-8"}),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> "ShiftHTML Chat",
        style >> LANDING_CSS,
    )

    page_body = body >> (
        iframe(src="/chat", classname="chat-frame"),
        iframe(src="/chat", classname="chat-frame"),
    )

    return html({"lang": "en"}) >> (page_head, page_body)


def chat_page(msgs: list[Message], username: str) -> html:
    async def load_messages():
        """Async component resolved during arender()."""
        return message_list(msgs)

    async def server_status():
        """Simulates a slow async fetch."""
        await asyncio.sleep(0.5)
        now = datetime.now()
        return div(classname="server-status") >> (span >> f"Server time: {now:%H:%M:%S}",)

    page_head = head >> (
        meta({"charset": "UTF-8"}),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> "ShiftHTML Chat",
        script(type="module", src=DATASTAR_CDN),
        link(rel="stylesheet", href="/static/style.css"),
    )

    header = div(classname="chat-header") >> (
        h1 >> "ShiftHTML Chat",
        span(classname="username") >> f"Chatting as {username}",
    )

    container = div(dict(data.init("@get('/feed')")), classname="chat-container") >> (
        header,
        load_messages,
        chat_input(),
        server_status,
    )

    page_body = body(dict(data.signals(username=username, messageInput=""))) >> container

    return html({"lang": "en"}) >> (page_head, page_body)


def message_list(msgs: list[Message]) -> div:
    children: list = [message_bubble(m) for m in msgs]
    if not children:
        children = [div(classname="empty-state") >> "No messages yet. Say hello!"]
    return div(id="messages", classname="messages") >> children


def message_bubble(msg: Message) -> div:
    msg_header = div(classname="message-header") >> (
        span(classname="message-username") >> msg.username,
        span(classname="message-time") >> msg.timestamp.strftime("%H:%M:%S"),
    )

    msg_text = div(classname="message-text") >> msg.text

    return div(classname="message") >> (msg_header, msg_text)


def chat_input() -> form:
    text_input = input_(
        dict(data.bind("messageInput")),
        type="text",
        placeholder="Type a message...",
        classname="message-input",
    )

    send_button = button(type="submit", classname="send-button") >> "Send"

    return form(
        dict(data.on("submit", "@post('/send')").prevent),
        classname="chat-input",
    ) >> (text_input, send_button)
