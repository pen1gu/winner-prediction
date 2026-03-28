import asyncio
import json
import sys
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sqlalchemy.orm import joinedload
from sqlmodel import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.models import MatchDetails, MatchInfos, MatchLogs
from server.app.models.session import AsyncSessionLocal


STATIC_DIR = Path(__file__).parent / "web_demo"
HOST = "127.0.0.1"
PORT = 8080


def iso_or_none(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


async def fetch_recent_matches(limit: int = 10) -> list[dict]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MatchLogs)
            .options(
                joinedload(MatchLogs.match_infos).joinedload(MatchInfos.home_team),
                joinedload(MatchLogs.match_infos).joinedload(MatchInfos.away_team),
                joinedload(MatchLogs.match_details),
            )
            .order_by(MatchLogs.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        matches = result.scalars().unique().all()

        payload: list[dict] = []
        for match in matches:
            info = match.match_infos
            home_detail = next((d for d in match.match_details if d.is_home), None)
            away_detail = next((d for d in match.match_details if not d.is_home), None)

            payload.append(
                {
                    "match_id": match.id,
                    "home_team": info.home_team.name if info and info.home_team else "Home",
                    "away_team": info.away_team.name if info and info.away_team else "Away",
                    "league_name": info.league_name if info else None,
                    "match_round": info.match_round if info else None,
                    "match_date": iso_or_none(info.match_date if info else None),
                    "finished": bool(info.finished) if info else False,
                    "stadium": info.stadium if info else None,
                    "score": {
                        "home": home_detail.score if home_detail else None,
                        "away": away_detail.score if away_detail else None,
                    },
                    "stats": {
                        "home_xg": home_detail.expected_goals_value if home_detail else None,
                        "away_xg": away_detail.expected_goals_value if away_detail else None,
                        "home_possession": home_detail.possession if home_detail else None,
                        "away_possession": away_detail.possession if away_detail else None,
                        "home_shots": home_detail.shots_total if home_detail else None,
                        "away_shots": away_detail.shots_total if away_detail else None,
                        "home_shots_on_target": home_detail.shots_on_target if home_detail else None,
                        "away_shots_on_target": away_detail.shots_on_target if away_detail else None,
                    },
                }
            )

        return payload


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
