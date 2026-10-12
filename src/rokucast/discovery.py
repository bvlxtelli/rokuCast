"""LAN discovery: SSDP/DIAL responder + mDNS _googlecast._tcp announcement."""

from __future__ import annotations

import socket
import struct
import threading


def ssdp_responder(stop: threading.Event, port: int, uuid: str, name: str):
    """Answer M-SEARCH (DIAL/UPnP) with LOCATION -> /ssdp/device-desc.xml."""
    from rokucast.ecp import local_ip

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", 1900))
    except OSError as e:
        print(f"[ssdp] sem bind :1900 ({e}); discovery DIAL limitado")
        return
    mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError as e:
        print(f"[ssdp] sem multicast ({e})")
    sock.settimeout(1.0)
    print("[ssdp] ouvindo M-SEARCH em :1900")
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(4096)
        except TimeoutError:
            continue
        except OSError:
            break
        text = data.decode(errors="ignore")
        if "M-SEARCH" not in text:
            continue
        location = f"http://{local_ip()}:{port}/ssdp/device-desc.xml"
        resp = "\r\n".join(
            [
                "HTTP/1.1 200 OK",
                "CACHE-CONTROL: max-age=1800",
                f"LOCATION: {location}",
                "SERVER: RokuCast/1.0 UPnP/1.0",
                "ST: urn:dial-multiscreen-org:service:dial:1",
                f"USN: uuid:{uuid}::urn:dial-multiscreen-org:service:dial:1",
                "",
                "",
            ]
        )
        try:
            sock.sendto(resp.encode(), addr)
            print(f"[ssdp] respondido {addr} -> {location} ({name})")
        except OSError:
            pass


def mdns_advertise(stop: threading.Event, name: str, port: int):
    """Announce _googlecast._tcp.local so Android/Chrome list this bridge."""
    try:
        from zeroconf import ServiceInfo, Zeroconf
    except ImportError:
        print(
            "[mdns] `zeroconf` nao instalado: pule o anuncio _googlecast._tcp "
            '(instale o extra: `uv pip install -e ".[mdns]"`). '
            "DIAL/SSDP continua funcionando."
        )
        return
    from rokucast.ecp import local_ip

    zc = Zeroconf()
    info = ServiceInfo(
        "_googlecast._tcp.local.",
        f"{name}._googlecast._tcp.local.",
        addresses=[socket.inet_aton(local_ip())],
        port=port,
        properties={
            b"md": name.encode(),
            b"fn": name.encode(),
            b"ca": b"5",
            b"st": b"0",
            b"rs": b"",
        },
        server=f"{socket.gethostname()}.local.",
    )
    zc.register_service(info)
    print(f"[mdns] anunciado {name}._googlecast._tcp.local :{port}")
    stop.wait()
    zc.unregister_service(info)
    zc.close()
