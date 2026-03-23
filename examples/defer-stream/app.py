# /// script
# dependencies = [
#   "flask",
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

from pathlib import Path

from components import page
from flask import Flask, Response, send_from_directory

from shifthtml import stream

app = Flask(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/")
def index():
    return Response(stream(page()), content_type="text/html")


if __name__ == "__main__":
    app.run(debug=True)
