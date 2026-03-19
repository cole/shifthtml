# /// script
# dependencies = [
#   "datastar-py",
#   "sanic",
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

import asyncio
import uuid
from pathlib import Path

from datastar_py.sanic import ServerSentEventGenerator as SSE
from datastar_py.sanic import datastar_respond, read_signals
from sanic import Sanic
from sanic.response import html

from components import Message, chat_page, landing_page, message_list
from shifthtml import shift

app = Sanic("ChatDatastar")
app.static("/static", Path(__file__).parent / "static")

messages: list[Message] = []


@app.get("/")
async def index(request):
    return html(str(shift(landing_page())))


@app.get("/chat")
async def chat(request):
    username = f"User-{uuid.uuid4().hex[:6]}"
    page = chat_page(messages, username)
    rendered = "".join([chunk async for chunk in shift(page).arender()])
    return html(rendered)


@app.post("/send")
async def send(request):
    signals = await read_signals(request) or {}
    username = signals.get("username", "Anonymous")
    text = signals.get("messageInput", "").strip()

    if text:
        messages.append(Message(username=username, text=text))

    response = await datastar_respond(request)
    await response.send(SSE.patch_signals({"messageInput": ""}))
    await response.eof()


@app.get("/feed")
async def feed(request):
    response = await datastar_respond(request)
    seen = len(messages)

    while True:
        await asyncio.sleep(0.1)
        if len(messages) > seen:
            seen = len(messages)
            rendered = str(shift(message_list(messages)))
            await response.send(SSE.patch_elements(rendered, selector="#messages"))
            await response.send(
                SSE.execute_script(
                    "document.getElementById('messages')"
                    ".scrollTo({top: document.getElementById('messages').scrollHeight,"
                    " behavior: 'smooth'})"
                )
            )


if __name__ == "__main__":
    app.run(dev=True)
