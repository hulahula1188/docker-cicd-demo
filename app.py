"""零依赖的最小 Web 服务：只用 Python 标准库，方便演示 Docker 打包。"""

import json
import os
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def greet(name: str) -> str:
    """纯逻辑函数，方便单元测试。"""
    name = (name or "").strip()
    if not name:
        return "Hello, stranger!"
    return f"Hello, {name}!"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/health"):
            self._send_json(200, {"status": "ok"})
            return

        if self.path.startswith("/hello"):
            name = ""
            if "?" in self.path:
                query = self.path.split("?", 1)[1]
                for pair in query.split("&"):
                    key, _, value = pair.partition("=")
                    if key == "name":
                        name = value
            self._send_json(200, {"message": greet(name)})
            return

        self._send_json(
            200,
            {
                "message": greet("Docker"),
                "hostname": socket.gethostname(),
                "time": datetime.now(timezone.utc).isoformat(),
                "hint": "试试 /health 和 /hello?name=你的名字",
            },
        )

    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)


def make_server(port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"listening on 0.0.0.0:{port}", flush=True)
    make_server(port).serve_forever()
