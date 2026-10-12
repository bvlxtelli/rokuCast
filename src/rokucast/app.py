"""Entry point: CLI + wiring (HTTP server, SSDP, mDNS, ECP push)."""

from __future__ import annotations

import argparse
import threading
from http.server import ThreadingHTTPServer

import rokucast.server as server
from rokucast.discovery import mdns_advertise, ssdp_responder
from rokucast.ecp import local_ip, roku_ecp_launch
from rokucast.state import State


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="rokuCast bridge: expoe o Roku como alvo de cast, toca via ECP"
    )
    p.add_argument("--roku-ip", default="", help="IP do Roku (vazio = so polling)")
    p.add_argument("--name", default="RokuCast", help="Nome exibido no menu Cast")
    p.add_argument("--port", type=int, default=8010, help="Porta HTTP do bridge")
    p.add_argument("--channel", default="dev", help="Channel ID ECP (dev = sideload)")
    p.add_argument("--uuid", default="rokuCast-0001", help="UDN DIAL")
    p.add_argument("--advertise-ip", default="", help="IP anunciado p/ a TV (auto-detect)")
    p.add_argument("--no-ssdp", action="store_true", help="Desliga responder SSDP")
    p.add_argument("--no-mdns", action="store_true", help="Desliga anuncio mDNS")
    return p.parse_args(argv)


def push_to_roku_async(state: State, media: dict) -> None:
    """Best-effort ECP push; the queue polling covers failures."""
    if not state.roku_ip:
        return  # TV pulls via polling once it knows bridgeUrl
    params = {
        "contentUrl": media.get("url", ""),
        "streamFormat": media.get("streamFormat", ""),
        "title": media.get("title", ""),
        "bridgeUrl": f"http://{state.advertise_ip or local_ip()}:{state.port}",
    }
    threading.Thread(
        target=roku_ecp_launch, args=(state.roku_ip, state.channel, params), daemon=True
    ).start()


def main(argv=None) -> None:
    args = parse_args(argv)
    state = State(
        name=args.name,
        roku_ip=args.roku_ip,
        channel=args.channel,
        port=args.port,
        uuid=args.uuid,
        advertise_ip=args.advertise_ip,
    )
    server.STATE = state
    server.ON_CAST = lambda media: push_to_roku_async(state, media)
    stop = threading.Event()

    if not args.no_ssdp:
        threading.Thread(
            target=ssdp_responder, args=(stop, state.port, state.uuid, state.name), daemon=True
        ).start()
    if not args.no_mdns:
        threading.Thread(
            target=mdns_advertise, args=(stop, state.name, state.port), daemon=True
        ).start()

    srv = ThreadingHTTPServer(("0.0.0.0", state.port), server.Handler)
    print(
        f"[bridge] {state.name} em http://{local_ip()}:{state.port} "
        f"-> Roku {state.roku_ip or '(polling)'}"
    )
    print("[bridge] POST /cast para enfileirar midia. Ctrl+C para sair.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        srv.server_close()
