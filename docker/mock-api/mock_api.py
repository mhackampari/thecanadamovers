import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            parsed = json.loads(body)
            print(f"[mock-api] payload: {json.dumps(parsed, indent=2)}")
        except Exception:
            print(f"[mock-api] raw body: {body.decode()}")

        # Simulate honeypot check
        if parsed.get("middle_name"):
            print("[mock-api] honeypot triggered — dropping silently")
            self._respond(200, {"ok": True})
            return

        print("[mock-api] returning ok=True (no email sent in local mode)")
        self._respond(200, {"ok": True})

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _respond(self, status: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        print(f"[mock-api] {format % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3001))
    print(f"[mock-api] listening on :{port}")
    HTTPServer(("", port), MockHandler).serve_forever()
