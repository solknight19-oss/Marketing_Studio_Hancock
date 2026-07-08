#!/usr/bin/env python3
import http.server
import json
import os
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "HancockIONTraining/1.0"

    def send_payload(self, data, content_type, code=200, cache="public, max-age=300"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload, code=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_payload(data, "application/json; charset=utf-8", code, "no-store")

    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path
        if route == "/healthz":
            self.send_json({"ok": True, "service": "hancock-ion-training"})
            return

        if route in ("", "/"):
            route = "/index.html"

        relative = route.lstrip("/")
        if not relative or ".." in Path(relative).parts:
            self.send_error(404)
            return

        target = (ROOT / relative).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_error(404)
            return

        if not target.exists() or not target.is_file():
            self.send_error(404)
            return

        cache = "public, max-age=31536000, immutable" if route.startswith("/assets/") else "public, max-age=300"
        content_type = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self.send_payload(target.read_bytes(), content_type, cache=cache)


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving ION training on {HOST}:{PORT}")
    server.serve_forever()
