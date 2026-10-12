"""Shared bridge state: the pending media queue.

The queue item ``{"url", "streamFormat", "title"}`` is the source of truth.
The bridge never fetches or stores media, it only passes URLs around:
enqueue via POST /cast (or DIAL launch), dequeue via GET /queue/next
(polled by the Roku channel's CastTask) plus a best-effort ECP push.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field


@dataclass
class State:
    name: str = "RokuCast"
    roku_ip: str = ""
    channel: str = "dev"
    port: int = 8010
    uuid: str = "rokuCast-0001"
    advertise_ip: str = ""
    pending: queue.Queue = field(default_factory=queue.Queue)
    last_media: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def enqueue(self, media: dict) -> None:
        self.pending.put(media)

    def dequeue(self) -> dict | None:
        try:
            media = self.pending.get_nowait()
        except queue.Empty:
            return None
        with self.lock:
            self.last_media = media
        return media
