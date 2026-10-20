"""BorderWise AI local web server. Uses only Python's standard library."""
from __future__ import annotations

import json
import os
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent import _local_fallback, audit_event
from finance_tools import calculate_student_budget, compare_transfer_quotes, public_tool_specs, execute_public_tool

ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "web" / "index.html"
HOST = "127.0.0.1"
PORT = int(os.getenv("BORDERWISE_PORT", "8501"))
AUDIT_LOG: list[dict[str, str]] = []
MAX_BODY_BYTES = 1_000_000


def _event(action: str, outcome: str) -> None:
    """Only event metadata is stored; user content and financial values are excluded."""
    AUDIT_LOG.append(audit_event(action, outcome))
    if len(AUDIT_LOG) > 300:
        del AUDIT_LOG[:-300]


def _llm_answer(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """Optional Chat Completions integration using urllib, so no SDK is required."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"answer": _local_fallback(message), "mode": "local-fallback", "tools_used": []}

    model = os.getenv("BORDERWISE_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
    system = (
        "You are BorderWise AI, a cross-border student finance planning assistant. "
        "Use approved calculator tools for calculations; never invent missing values. "
        "All costs and exchange rates are user assumptions; this app has no live FX or official immigration data. "
        "For visa/proof-of-funds/legal questions, direct the user to the relevant official authority. "
        "Never ask for passwords, PINs, OTPs, full card numbers, bank credentials or passport scans. "
        "Never initiate payments, transfers, applications, or account changes. This agent is read-only. "
        "Clearly explain assumptions and limitations."
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for item in history[-8:]:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str):
            messages.append({"role": item["role"], "content": item["content"][:3000]})
    messages.append({"role": "user", "content": message[:3000]})
    tools_used: list[str] = []

    try:
        for _ in range(4):
            payload = {
                "model": model,
                "messages": messages,
                "tools": public_tool_specs(),
                "tool_choice": "auto",
                "temperature": 0.1,
            }
            req = Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode("utf-8"))
            choice = data["choices"][0]["message"]
            tool_calls = choice.get("tool_calls") or []
            if not tool_calls:
                return {
                    "answer": choice.get("content") or "I could not produce a response. Please try again.",
                    "mode": "llm+tools",
                    "tools_used": tools_used,
                }
            messages.append({
                "role": "assistant",
                "content": choice.get("content"),
                "tool_calls": tool_calls,
            })
            for tool_call in tool_calls:
                name = tool_call.get("function", {}).get("name", "")
                try:
                    args = json.loads(tool_call.get("function", {}).get("arguments") or "{}")
                    result = execute_public_tool(name, args)
                    tools_used.append(name)
                    output = {"ok": True, "result": result}
                except Exception as exc:
                    output = {"ok": False, "error": str(exc)}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "content": json.dumps(output, ensure_ascii=False)[:10000],
                })
        return {"answer": "I reached the tool-call limit. Please narrow your question and try again.", "mode": "llm+tools", "tools_used": tools_used}
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
        # Keep the browser response free of provider error details and credentials.
        return {
            "answer": _local_fallback(message) + "\n\n(The model service was unavailable, so I used local guidance instead.)",
            "mode": "local-fallback",
            "tools_used": [],
            "notice": type(exc).__name__,
        }
    except Exception as exc:  # defensive fallback for SDK/API response shape changes
        return {
            "answer": _local_fallback(message) + "\n\n(The model service was unavailable, so I used local guidance instead.)",
            "mode": "local-fallback",
            "tools_used": [],
            "notice": type(exc).__name__,
        }


def process_api(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """Testable API dispatcher used by HTTP handler and unit tests."""
    payload = payload or {}
    if method == "GET" and path == "/api/health":
        has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
        return 200, {
            "ok": True,
            "app": "BorderWise AI",
            "mode": "llm+tools" if has_key else "local demo",
            "llm_configured": has_key,
            "port": PORT,
        }
    if method == "GET" and path == "/api/audit":
        return 200, {"events": AUDIT_LOG}
    if method != "POST":
        return 405, {"error": "Method not allowed"}
    if not isinstance(payload, dict):
        return 400, {"error": "Request body must be a JSON object"}

    try:
        if path == "/api/budget":
            result = calculate_student_budget(**payload)
            _event("budget_calculation", "success")
            return 200, {"ok": True, "result": result}
        if path == "/api/transfer":
            result = compare_transfer_quotes(**payload)
            _event("transfer_quote_comparison", "success")
            return 200, {"ok": True, "result": result}
        if path == "/api/chat":
            message = payload.get("message")
            if not isinstance(message, str) or not message.strip():
                return 400, {"error": "Please enter a question."}
            history = payload.get("history", [])
            if not isinstance(history, list):
                history = []
            result = _llm_answer(message.strip(), history)
            _event("chat_message", result.get("mode", "completed"))
            return 200, {"ok": True, "result": result}
        return 404, {"error": "API endpoint not found"}
    except (TypeError, ValueError, KeyError) as exc:
        _event(path.strip("/"), "validation_error")
        return 400, {"error": str(exc)}
    except Exception:
        _event(path.strip("/"), "internal_error")
        return 500, {"error": "The request could not be completed. Check the input and try again."}


class BorderWiseHandler(BaseHTTPRequestHandler):
    server_version = "BorderWiseLocal/1.0"

    def _send(self, status: int, data: bytes, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                content = INDEX_FILE.read_bytes()
            except OSError:
                self._send(500, b"BorderWise UI file is missing.", "text/plain; charset=utf-8")
                return
            self._send(200, content, "text/html; charset=utf-8")
            return
        if path.startswith("/api/"):
            status, body = process_api("GET", path)
            self._send(status, json.dumps(body, ensure_ascii=False).encode("utf-8"))
            return
        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, b'{"error":"Invalid content length"}')
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self._send(413, b'{"error":"Request body too large"}')
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, b'{"error":"Invalid JSON request body"}')
            return
        status, body = process_api("POST", path, payload)
        self._send(status, json.dumps(body, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        # Keep terminal logs concise; never print request bodies.
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.address_string()} - {format % args}")


def main() -> None:
    global PORT
    candidates = [PORT] + list(range(PORT + 1, min(PORT + 11, 65536)))
    httpd = None
    for candidate in candidates:
        try:
            httpd = ThreadingHTTPServer((HOST, candidate), BorderWiseHandler)
            PORT = int(httpd.server_address[1])
            if candidate != candidates[0]:
                print(f"Port {candidates[0]} was already in use; using port {PORT} instead.")
            break
        except OSError:
            continue
    if httpd is None:
        raise OSError(f"Could not find a free localhost port between {candidates[0]} and {candidates[-1]}.")
    url = f"http://{HOST}:{PORT}"
    print("=" * 62)
    print("BorderWise AI is running locally")
    print(f"Open: {url}")
    print("Mode:", "LLM + approved calculator tools" if os.getenv("OPENAI_API_KEY", "").strip() else "Local demo (no API key needed)")
    print("Privacy: server binds to 127.0.0.1; no account or payment access")
    print("Press Ctrl+C to stop.")
    print("=" * 62)
    if os.getenv("BORDERWISE_NO_BROWSER") != "1":
        timer = threading.Timer(1.0, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping BorderWise AI...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
