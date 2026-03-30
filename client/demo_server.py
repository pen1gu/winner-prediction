import asyncio
import json
import sys
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.models.session import AsyncSessionLocal
from server.app.store.db_query import fetch_recent_match_summaries


STATIC_DIR = Path(__file__).parent / "web_demo"
HOST = "127.0.0.1"
PORT = 8080


def iso_or_none(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


async def fetch_recent_matches(limit: int = 10) -> list[dict]:
    async with AsyncSessionLocal() as session:
        raw = await fetch_recent_match_summaries(session, limit=limit)
    out = []
    for row in raw:
        row = dict(row)
        md = row.get("match_date")
        row["match_date"] = iso_or_none(md) if md is not None else None
        out.append(row)
    return out


def run_async(coro):
    return asyncio.run(coro)


class DemoRequestHandler(BaseHTTPRequestHandler):
    def _write_json(self, data: dict | list, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, relative_path: str) -> None:
        path = STATIC_DIR / relative_path
        if not path.exists() or not path.is_file():
            self.send_error(404, "File not found")
            return

        if path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        else:
            content_type = "application/octet-stream"

        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/":
            self._serve_file("index.html")
            return
        if route.startswith("/static/"):
            rel = route[len("/static/") :].lstrip("/")
            if not rel or ".." in rel:
                self.send_error(404, "Not Found")
                return
            self._serve_file(rel)
            return
        if route == "/app.js":
            self._serve_file("app.js")
            return
        if route == "/styles.css":
            self._serve_file("styles.css")
            return
        if route == "/api/health":
            self._write_json({"ok": True, "message": "demo server is running"})
            return
        if route == "/api/matches/latest":
            try:
                query = parse_qs(parsed.query)
                limit = int(query.get("limit", ["10"])[0])
                limit = max(1, min(30, limit))
                matches = run_async(fetch_recent_matches(limit=limit))
                self._write_json({"ok": True, "count": len(matches), "matches": matches})
            except Exception as exc:
                traceback.print_exc()
                self._write_json(
                    {"ok": False, "error": str(exc), "message": "데이터 조회 중 오류가 발생했습니다."},
                    status=500,
                )
            return

        self.send_error(404, "Not Found")

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    if not STATIC_DIR.exists():
        raise FileNotFoundError(f"정적 파일 폴더를 찾을 수 없습니다: {STATIC_DIR}")

    server = HTTPServer((HOST, PORT), DemoRequestHandler)
    print(f"Demo server started: http://{HOST}:{PORT}")
    print("Ctrl+C 로 종료할 수 있습니다.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Demo server stopped.")


if __name__ == "__main__":
    main()
