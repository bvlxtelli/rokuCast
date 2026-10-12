"""HTTP layer: DIAL/SSDP descriptor, queue API and status page (stdlib only)."""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler

from rokucast.media import guess_format
from rokucast.state import State

DEVICE_DESC = """<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion><major>1</major><minor>0</minor></specVersion>
  <device>
    <deviceType>urn:dial-multiscreen-org:device:dial:1</deviceType>
    <friendlyName>{name}</friendlyName>
    <manufacturer>RokuCast</manufacturer>
    <modelName>RokuCast Bridge</modelName>
    <UDN>uuid:{uuid}</UDN>
  </device>
</root>"""

DIAL_APP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<service xmlns="urn:dial-multiscreen-org:schemas:dial">
  <name>{app}</name>
  <options allowStop="true"/>
  <state>{state}</state>
</service>"""

DRM_APPS = ("youtube", "netflix")

# Set by app.main before serving; keeps the handler signature stdlib-plain.
STATE: State | None = None
ON_CAST: Callable[[dict], None] | None = None


class Handler(BaseHTTPRequestHandler):
    server_version = "RokuCast/1.0"

    def log_message(self, fmt, *args):
        print(f"[http] {self.address_string()} {fmt % args}")

    # -- helpers
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _xml(self, text, code=200):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text, code=200):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- routes
    def do_GET(self):
        assert STATE is not None
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            return self._html(status_page(STATE))
        if path == "/ssdp/device-desc.xml":
            return self._xml(DEVICE_DESC.format(name=STATE.name, uuid=STATE.uuid))
        if path == "/status":
            with STATE.lock:
                last = dict(STATE.last_media)
            return self._json(
                {
                    "name": STATE.name,
                    "roku_ip": STATE.roku_ip,
                    "queue": STATE.pending.qsize(),
                    "last": last,
                }
            )
        if path == "/queue/next":
            media = STATE.dequeue()
            return self._json(media if media is not None else {"url": ""})
        if path.startswith("/apps/"):
            app = path[len("/apps/") :] or "YouTube"
            return self._xml(DIAL_APP_XML.format(app=app, state="stopped"))
        return self._json({"error": "not-found"}, 404)

    def do_POST(self):
        assert STATE is not None
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""

        if path == "/cast":
            try:
                data = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                return self._json({"error": "json invalido"}, 400)
            url = data.get("url", "")
            if not url:
                return self._json({"error": "campo 'url' obrigatorio"}, 400)
            media = {
                "url": url,
                "streamFormat": data.get("streamFormat") or guess_format(url),
                "title": data.get("title", ""),
            }
            STATE.enqueue(media)
            if ON_CAST is not None:
                ON_CAST(media)
            return self._json({"ok": True, "queued": media})

        if path.startswith("/apps/"):
            # DIAL launch, e.g. POST /apps/YouTube with `v=<videoId>`.
            # Leanback/DRM apps are not translatable to a plain URL -> honest 501.
            app = path[len("/apps/") :]
            qs = urllib.parse.parse_qs(parsed.query)
            body = raw.decode(errors="replace")
            lowered = (app + " " + body).lower()
            if any(k in lowered for k in DRM_APPS):
                return self._json(
                    {
                        "error": f"{app}: launch DIAL recebido, mas app com DRM "
                        "nao e traduzivel p/ URL. Use POST /cast com HLS/MP4 "
                        "ou o Screen Mirroring nativo do Roku."
                    },
                    501,
                )
            for key in ("url", "contentUrl", "mediaUrl"):
                if key in qs:
                    media = {
                        "url": qs[key][0],
                        "streamFormat": guess_format(qs[key][0]),
                        "title": app,
                    }
                    STATE.enqueue(media)
                    if ON_CAST is not None:
                        ON_CAST(media)
                    return self._json({"ok": True, "queued": media}, 201)
            return self._json(
                {"ok": True, "app": app, "note": "DIAL registrado; envie /cast p/ tocar"}, 201
            )

        return self._json({"error": "not-found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    do_DELETE = do_POST  # DIAL uses DELETE /apps/X/run to stop


def status_page(st: State) -> str:
    with st.lock:
        last = st.last_media
    return f"""<h1>rokuCast bridge ok</h1>
<p>Anunciado como: <b>{st.name}</b> | Roku: <b>{st.roku_ip or "(polling apenas)"}</b></p>
<p>Fila: {st.pending.qsize()} | Ultimo: {last}</p>
<pre>curl -X POST http://localhost:{st.port}/cast -H "Content-Type: application/json" -d '{{"url":"https://SEU_VIDEO.m3u8","title":"Teste"}}'</pre>
<p>DIAL desc: <a href="/ssdp/device-desc.xml">/ssdp/device-desc.xml</a> | JSON: <a href="/status">/status</a></p>"""
