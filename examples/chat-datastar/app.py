# /// script
# dependencies = [
#   "datastar-py",
#   "litestar[standard]",
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

import asyncio
import uuid
from pathlib import Path

from components import Message, message_list
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.litestar import DatastarResponse, read_signals
from litestar import Litestar, Request, get, post
from litestar.response import Stream
from litestar.static_files import create_static_files_router
from pages import chat_page, landing_page

from shifthtml import astream, render

messages: list[Message] = []


@get("/")
async def index() -> Stream:
    return Stream(astream(landing_page()), media_type="text/html")


@get("/chat")
async def chat() -> Stream:
    username = f"User-{uuid.uuid4().hex[:6]}"
    page = chat_page(messages, username)
    return Stream(astream(page), media_type="text/html")


@post("/send")
async def send(request: Request) -> DatastarResponse:
    signals = await read_signals(request) or {}
    username = signals.get("username", "Anonymous")
    text = signals.get("messageInput", "").strip()

    if text:
        messages.append(Message(username=username, text=text))

    return DatastarResponse(SSE.patch_signals({"messageInput": ""}))


@get("/feed")
async def feed(request: Request) -> DatastarResponse:
    async def generate():
        seen = len(messages)
        while True:
            await asyncio.sleep(0.1)
            if len(messages) > seen:
                seen = len(messages)
                rendered = render(message_list(messages))
                yield SSE.patch_elements(rendered, selector="#messages")
                yield SSE.execute_script(
                    "document.getElementById('messages')"
                    ".scrollTo({top: document.getElementById('messages').scrollHeight,"
                    " behavior: 'smooth'})"
                )

    return DatastarResponse(generate())


static_files = create_static_files_router(path="/static", directories=[Path(__file__).parent / "static"])

app = Litestar(route_handlers=[index, chat, send, feed, static_files])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", reload=True)
