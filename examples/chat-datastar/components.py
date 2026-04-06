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
        children = [div(class_="empty-state") >> "No messages yet. Say hello!"]
    return div(id="messages", class_="messages") >> children


def message_bubble(msg: Message) -> div:
    msg_header = div(class_="message-header") >> (
        span(class_="message-username") >> msg.username,
        span(class_="message-time") >> msg.timestamp.strftime("%H:%M:%S"),
    )
    msg_text = div(class_="message-text") >> msg.text

    return div(class_="message") >> (msg_header, msg_text)


def chat_input() -> form:
    text_input = input_(
        dict(data.bind("messageInput")),
        type="text",
        placeholder="Type a message...",
        class_="message-input",
    )
    send_button = button(type="submit", class_="send-button") >> "Send"

    return form(
        dict(data.on("submit", "@post('/send'); $messageInput=''").prevent),
        class_="chat-input",
    ) >> (text_input, send_button)
