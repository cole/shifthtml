from __future__ import annotations

import asyncio
from datetime import datetime

from components import Message, chat_input, message_list
from datastar_py import attribute_generator as data

from shifthtml import (
    body,
    div,
    h1,
    head,
    html,
    iframe,
    link,
    meta,
    script,
    span,
    title,
)

DATASTAR_CDN = "https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js"


def landing_page() -> html:
    page_head = head() >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title() >> "ShiftHTML Chat",
        link(rel="stylesheet", href="/static/landing.css"),
    )
    page_body = body() >> (
        iframe(src="/chat", class_="chat-frame"),
        iframe(src="/chat", class_="chat-frame"),
    )

    return html(lang="en") >> (page_head, page_body)


def chat_page(msgs: list[Message], username: str) -> html:
    async def load_messages():
        """Async component resolved during astream()."""
        return message_list(msgs)

    async def server_status():
        """Simulates a slow async fetch."""
        await asyncio.sleep(0.5)
        now = datetime.now()
        return div(class_="server-status") >> (span() >> f"Server time: {now:%H:%M:%S}",)

    page_head = head() >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title() >> "ShiftHTML Chat",
        script(type="module", src=DATASTAR_CDN),
        link(rel="stylesheet", href="/static/style.css"),
    )

    chat_header = div(class_="chat-header") >> (
        h1() >> "ShiftHTML Chat",
        span(class_="username") >> f"Chatting as {username}",
    )

    container = div(dict(data.init("@get('/feed')")), class_="chat-container") >> (
        chat_header,
        load_messages,
        chat_input(),
        server_status,
    )

    page_body = body(dict(data.signals(username=username, messageInput=""))) >> container

    return html(lang="en") >> (page_head, page_body)
