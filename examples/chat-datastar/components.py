from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from datastar_py import attribute_generator as data

from shifthtml import button, div, form, input_, span


@dataclass
class Message:
    username: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)


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
