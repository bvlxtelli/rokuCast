"""Roku ECP client (External Control Protocol, port 8060)."""

from __future__ import annotations

import socket
import urllib.parse
import urllib.request


def local_ip() -> str:
    """Best-guess LAN IP so the TV can reach the bridge back."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def roku_ecp_launch(roku_ip: str, channel: str, params: dict) -> bool:
    """Fire an ECP launch: POST http://roku:8060/launch/<channel>?k=v..."""
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    url = f"http://{roku_ip}:8060/launch/{channel}?{qs}"
    req = urllib.request.Request(url, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print(f"[ecp] launch {r.status} -> {url}")
            return 200 <= r.status < 300
    except Exception as e:  # noqa: BLE001 - log and continue, polling covers it
        print(f"[ecp] failed ({e}) -> {url}")
        return False
