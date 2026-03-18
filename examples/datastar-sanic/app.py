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
from datetime import datetime

from components import page, time_element
from datastar_py.sanic import ServerSentEventGenerator as SSE
from datastar_py.sanic import datastar_respond
from sanic import Sanic
from sanic.response import html

from shifthtml import shift

app = Sanic("ShiftDatastar")


@app.get("/")
async def index(request):
    now = datetime.now().isoformat()
    return html(str(shift(page(now))))


@app.get("/updates")
async def updates(request):
    response = await datastar_respond(request)

    while True:
        now = datetime.now().isoformat()
        await response.send(
            SSE.patch_elements(
                str(shift(time_element(now))),
                selector="#time-element",
            )
        )
        await asyncio.sleep(1)
        await response.send(SSE.patch_signals({"currentTime": datetime.now().isoformat()}))
        await asyncio.sleep(1)


if __name__ == "__main__":
    app.run(dev=True)
