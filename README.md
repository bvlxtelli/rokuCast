# rokuCast

Your Roku TV as a native Android cast target: discover it like a Chromecast, play plain-URL media (MP4/HLS/DASH) on the big screen.

[Report Bug](https://github.com/bvlxtelli/rokuCast/issues/new?labels=bug&title=%5BBug%5D+Simple+description+of+the+bug) · [Request Feature](https://github.com/bvlxtelli/rokuCast/issues/new?labels=enhancement&title=%5BFeature%5D+Simple+description+of+your+request)

[![Forks](https://img.shields.io/github/forks/bvlxtelli/rokuCast?style=for-the-badge)](https://github.com/bvlxtelli/rokuCast/network/members) [![Stargazers](https://img.shields.io/github/stars/bvlxtelli/rokuCast?style=for-the-badge)](https://github.com/bvlxtelli/rokuCast/stargazers) [![Issues](https://img.shields.io/github/issues/bvlxtelli/rokuCast?style=for-the-badge)](https://github.com/bvlxtelli/rokuCast/issues)

## About The Project

rokuCast makes a **Roku TV show up as a cast target for Android** (Chromecast-style)
for media you already have a direct URL for — MP4 files, HLS/DASH lives, your own
server, Jellyfin/Plex share links.

Works like [Hydra Launcher](https://github.com/hydralauncher/hydra): the app ships with
**no streams, no URLs, no accounts, no DRM bypass**. You bring your own media URLs;
rokuCast moves the URL to the TV.

How it works: a Python **bridge** on your LAN (PC/Raspberry) emulates Chromecast
discovery (mDNS `_googlecast._tcp` + SSDP/DIAL) and translates each cast into what
Roku understands — an ECP `launch` plus a SceneGraph **receiver channel** with a
`Video` node. The WFD/RTSP mapping idea comes from
[MiracleCast](https://github.com/albfan/miraclecast); the limits are honest and
documented below.

Features:

-   Discover
    -   Shows up in the Android/Chrome Cast menu (mDNS) and answers DIAL/SSDP `M-SEARCH`.
    -   No root, no Wi-Fi Direct, no firmware mod — bridge + sideloaded channel only.
-   Cast
    -   `POST /cast {"url","title"}` queues media; Roku gets an instant ECP push
        with polling (`GET /queue/next`) as fallback so casts are never lost.
    -   Auto-detects `streamformat` (`hls`/`dash`/`mp4`) from the URL.
-   Receiver
    -   SceneGraph channel plays the URL via the `Video` node, handles DIAL/ECP
        launches (`roInputEvent`) while in foreground.
-   Honest limits
    -   **No DRM**: Netflix/Prime/signed-in YouTube answer `501` — use the Roku's
        native apps or native Screen Mirroring instead.
    -   **No screen mirroring through this bridge** — the Roku already *is* a
        Miracast sink (Settings → System → Screen mirroring); use that.

### Built With

-   [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
-   [![BrightScript](https://img.shields.io/badge/BrightScript-SceneGraph-662D91?style=for-the-badge)](https://developer.roku.com/dev/docs/brightscript-language-reference)
-   [![uv](https://img.shields.io/badge/uv-packages-4B275F?style=for-the-badge)](https://docs.astral.sh/uv/)

## Changelog

### v0.1.0

-   First release: bridge (`POST /cast`, `/queue/next`, DIAL/SSDP desc, mDNS, ECP push) + SceneGraph receiver channel (Video + polling task).

## Getting Started

### Prerequisites

-   Windows 10 or newer (bridge also runs on Linux/Raspberry).
-   A Roku on the same Wi-Fi, with [developer mode](https://developer.roku.com/docs/developer-program/getting-started/developer-setup.md) enabled (for the sideloaded receiver).
-   The Roku's IP (Settings → Network → About).
-   Your own media URLs (MP4/HLS/DASH without DRM).

### Installation (receiver on the TV)

1.  Head over to the [latest release](https://github.com/bvlxtelli/rokuCast/releases/latest)
2.  Download `rokuCast-channel-vX.Y.Z.zip`
3.  Sideload it at `http://<ROKU-IP>/` (dev installer, user `rokudev`)
4.  Open the **rokuCast** channel once on the TV (it must be in foreground to receive).

From source instead: zip the contents of `roku-channel/` yourself
(`manifest` at the zip root) and sideload that.

### First steps

1.  Start the bridge (same network as TV and phone):
    `uv run rokucast --roku-ip 192.168.1.50 --name "Sala (Roku)"`
2.  Cast something you own the URL of:
    `curl -X POST http://localhost:8010/cast -H "Content-Type: application/json" -d "{\"url\":\"https://SEU_VIDEO.m3u8\",\"title\":\"Demo\"}"`
3.  The TV plays it. Check `http://localhost:8010/status` anytime.

> New here? Full consumer walkthrough (TV install, bridge, local files,
> Android, troubleshooting): [`docs/USAGE.md`](docs/USAGE.md).

Local files? Serve them first (`python -m http.server 8080 --directory "E:\Videos"`)
and cast the `http://<SEU-PC>:8080/filme.mp4` URL — the Roku must reach the URL directly.

### Installation (from source)

1.  Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2.  `uv venv && uv pip install -e ".[dev]"`
3.  `uv run rokucast --help` to see options (`--roku-ip`, `--name`, `--port`, `--no-mdns`, `--no-ssdp`)
4.  mDNS menu listing needs the extra: `uv pip install -e ".[mdns]"`

Developers: `uv run ruff check src`, `uv run ruff format --check src`,
`uv run pytest -q` (CI runs lint + format + smoke import on `src`).

## Help links

-   Consumer guide (how to install, cast, fix): [`docs/USAGE.md`](docs/USAGE.md)
-   Roku dev setup: [developer-setup](https://developer.roku.com/docs/developer-program/getting-started/developer-setup.md)
-   BrightScript reference: [brightscript-language-reference](https://developer.roku.com/dev/docs/brightscript-language-reference)
-   The projects rokuCast builds on: [MiracleCast](https://github.com/albfan/miraclecast), [Hydra Launcher](https://github.com/hydralauncher/hydra)
-   Stuck? [Open an issue](https://github.com/bvlxtelli/rokuCast/issues) — bridge logs + `GET /status` output help a lot

## License

Distributed under the AGPL-3.0 License. See `LICENSE` for more information.

## Credits

-   WFD/sink pattern + RTSP mapping idea: [MiracleCast](https://github.com/albfan/miraclecast) by David Herrmann, Alberto Fanjul + contributors
-   Receiver/ECP/DIAL behavior: [Roku docs](https://developer.roku.com/) + [DIAL](https://www.dial-multiscreen.org/)
-   Bring-your-own-media model: [Hydra Launcher](https://github.com/hydralauncher/hydra)
-   Full list with licenses: [`docs/CREDITS.md`](docs/CREDITS.md)

## Community

rokuCast is 100% open source and counts on you: testing, issues, new sender
examples, docs and code.
Rule for contributions: no streams, no links, no DRM bypasses, no credentials,
no device IPs — same as the app.

## Contact

-   Issues: [bvlxtelli/rokuCast](https://github.com/bvlxtelli/rokuCast/issues)
-   More: [@bvlxtelli](https://github.com/bvlxtelli)
