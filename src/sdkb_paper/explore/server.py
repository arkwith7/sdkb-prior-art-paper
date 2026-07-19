"""로컬 진단 웹앱 — 표준 http.server 기반(신규 의존 0).

    python -m sdkb_paper.explore.server [--port 8000] [--host 127.0.0.1]

읽기 전용이다. 어떤 엔드포인트도 그래프를 쓰지 않는다.
"""
from __future__ import annotations

import argparse
import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from sdkb_paper.config import QUERIES_CQ
from sdkb_paper.explore import findings, store

STATIC = Path(__file__).parent / "static"

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def list_cqs() -> list[dict]:
    """queries/cq/*.rq 를 desc·expect-min 메타와 함께 나열한다(질의 프리셋)."""
    out = []
    for rq in sorted(QUERIES_CQ.glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        desc, expect_min = "", 1
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("# desc:"):
                desc = s.removeprefix("# desc:").strip()
            elif s.startswith("# expect-min:"):
                try:
                    expect_min = int(s.removeprefix("# expect-min:").strip())
                except ValueError:
                    pass
            elif s and not s.startswith("#"):
                break
        out.append({"name": rq.stem, "desc": desc, "expect_min": expect_min, "sparql": text})
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "sdkb-explore/1.0"

    # --- 응답 헬퍼 -------------------------------------------------------
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg, status=400):
        self._json({"error": msg}, status=status)

    def _static(self, rel: str):
        rel = rel.lstrip("/") or "index.html"
        path = (STATIC / rel).resolve()
        if not str(path).startswith(str(STATIC.resolve())) or not path.is_file():
            self._error("not found", 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _MIME.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- 라우팅 ---------------------------------------------------------
    def do_GET(self):
        route = urlparse(self.path).path
        try:
            if route in ("/", "/index.html"):
                self._static("index.html")
            elif route == "/api/status":
                self._json(self._status())
            elif route == "/api/cq":
                self._json({"cqs": list_cqs()})
            elif route == "/api/findings":
                self._json(findings.findings())
            elif route.startswith("/static/"):
                self._static(route.removeprefix("/static/"))
            else:
                self._static(route)
        except Exception as exc:  # noqa: BLE001 — 진단 도구는 스택을 클라이언트에 보낸다
            self._error(f"{exc}\n{traceback.format_exc()}", 500)

    def do_POST(self):
        route = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if route == "/api/sparql":
                self._json(self._sparql(payload))
            else:
                self._error("unknown route", 404)
        except json.JSONDecodeError:
            self._error("invalid JSON body")
        except Exception as exc:  # noqa: BLE001
            self._error(f"{type(exc).__name__}: {exc}", 400)

    # --- 엔드포인트 구현 ------------------------------------------------
    def _status(self) -> dict:
        graphs = store.available()
        sigs = {}
        for key, info in graphs.items():
            if info["exists"]:
                sigs[key] = findings.signature(key)
        return {"graphs": graphs, "signatures": sigs, "expected": findings.EXPECTED}

    def _sparql(self, payload: dict) -> dict:
        key = payload.get("graph", "v0")
        query = (payload.get("query") or "").strip()
        if not query:
            raise ValueError("빈 쿼리")
        return store.run_query(key, query).to_dict()

    def log_message(self, fmt, *args):  # 조용히 — 콘솔 노이즈 억제
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    # 요청 포트가 점유돼 있으면(EADDRINUSE) 이어지는 포트를 몇 개 시도한다.
    # WSL2 등에서 8000 이 우리 밖 프로세스에 잡혀 있는 경우가 흔하다.
    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingHTTPServer((host, p), Handler)
            port = p
            break
        except OSError as exc:
            if exc.errno != 98:  # EADDRINUSE 외의 오류는 그대로 던진다
                raise
            print(f"  포트 {p} 사용 중 — 다음 포트 시도…", flush=True)
    if httpd is None:
        raise SystemExit(
            f"{port}–{port + 9} 모두 사용 중. 빈 포트를 지정하라: make serve PORT=8080"
        )
    print(f"▶ SDKB 온톨로지 탐색기 — http://{host}:{port}", flush=True)
    print("  그래프는 첫 질의 시 지연 적재된다. Ctrl-C 로 종료.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n종료.")
        httpd.shutdown()


def main() -> None:
    ap = argparse.ArgumentParser(description="SDKB 온톨로지 탐색·모니터링 로컬 웹앱")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
