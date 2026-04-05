# /// script
# dependencies = [
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from components import page

STATIC_DIR = Path(__file__).parent / "static"

CONTENT_TYPES = {
    ".css": "text/css",
    ".js": "text/javascript",
}

request_count = 0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/static/"):
            self.serve_static()
        else:
            self.serve_page()

    def serve_page(self):
        global request_count
        request_count += 1

        content = page(request_count=request_count).stream()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        for chunk in content:
            self.wfile.write(chunk.encode())

    def serve_static(self):
        rel = self.path.removeprefix("/static/")
        file_path = STATIC_DIR / rel

        if not file_path.is_file() or STATIC_DIR not in file_path.resolve().parents:
            self.send_error(404)
            return

        content_type = CONTENT_TYPES.get(file_path.suffix, "application/octet-stream")
        data = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        print(f"  {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), Handler)
    print("Kitchen Sink → http://localhost:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
