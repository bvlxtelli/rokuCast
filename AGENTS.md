# AGENTS.md — rokuCast contributor guide

## Idea

rokuCast makes a **Roku TV show up as a native Android cast target**
(Chromecast-style) for **plain-URL media** (MP4/HLS/DASH files and lives):
a Python bridge on the LAN emulates discovery (mDNS `_googlecast._tcp` +
SSDP/DIAL) and translates casts into what Roku understands
(ECP `launch` + a SceneGraph receiver channel with a `Video` node).

Like Hydra, the app ships **no streams, no URLs, no DRM bypass, no keys**.
The user brings their own media URLs; rokuCast moves the URL to the TV.
DRM apps (Netflix/Prime/YouTube-signed-in) are answered with an honest
`501`, and live screen mirroring stays on the Roku's **native**
Screen Mirroring (Miracast sink) — never through this bridge.

## Source of truth

**The queue item is the source of truth — never the DIAL app state.**
`{"url", "streamFormat", "title"}` is enqueued via `POST /cast`
(or DIAL launch with a media param) and dequeued via `GET /queue/next`,
which the channel's `CastTask` polls. The bridge never fetches, stores
or transcodes media — it only passes URLs. DIAL `/apps/*` state
(`stopped`) is discovery cosmetics only.

## Architecture

- `src/rokucast/` — backend, stdlib-only (must never require new deps
  without a `docs/` row):
  - `media.py` — `guess_format()` (URL → `Video.streamformat`) +
    `MiracleTranslator` (WFD M1–M7 → Roku mapping, documented)
  - `state.py` — `State`: pending queue + `last_media` (+ lock);
    `enqueue()`/`dequeue()` are the only queue access
  - `server.py` — `Handler` (DIAL desc, `/cast`, `/queue/next`,
    `/status`, DIAL `/apps/*` with DRM `501`); module globals
    `STATE`/`ON_CAST` are set once by `app.main`
  - `discovery.py` — SSDP `M-SEARCH` responder + mDNS
    `_googlecast._tcp` announce (graceful without `zeroconf`)
  - `ecp.py` — `local_ip()` + `roku_ecp_launch()` (port 8060)
  - `app.py` — CLI + wiring (server/SSDP/mDNS/ECP push);
    `__main__.py` — entry (`uv run rokucast`, PyInstaller-safe)
- `roku-channel/` — BrightScript receiver (SceneGraph):
  - `source/main.brs` — entry + `roInputEvent` (DIAL/ECP launches)
  - `components/MainScene.xml/.brs` — `Video` + `handleLaunchArgs`
  - `components/CastTask.xml/.brs` — polls `GET {bridge}/queue/next`

## Validated live (don't regress)

- Roundtrip proven: `POST /cast {url}` → `GET /queue/next` returns the
  media once, second read is empty (`{"url": ""}`), DIAL desc returns 200.
- ECP launch contract: `POST http://ROKU:8060/launch/dev?contentUrl=…
  &streamFormat=hls&title=…&bridgeUrl=…` reaches `handleLaunchArgs`.
- Public no-DRM probes: `test-streams.mux.dev` HLS + `BigBuckBunny.mp4`.

## Rules

1. **No streams, links, credentials, keys, device IPs** in code, issues,
   PRs, releases. User-local data lives in `.rokucast/` (gitignored).
   Same Hydra-style rule as the app: bring your own URLs.
2. **Credit everything**: new dep/logic → row in `docs/CREDITS.md` +
   `docs/THIRD_PARTY.md` before merge. Repo is AGPL-3.0-or-later.
3. `tests/` stays local-only (gitignored) but must pass: `pytest -q`.
   CI covers `src` only (ruff + format + smoke import) for this reason.
4. Lint is law: `ruff check`, `ruff format --check` (CI enforces on `src`).
   Config: `pyproject.toml` (`E4/E7/E9/F/I/UP/B`).
5. Threads for all I/O (server/SSDP/mDNS/ECP push are daemon threads);
   bridge failures must never lose the cast — the queue polling covers them.
6. No DRM workarounds, no CastV2 device-auth spoofing, no token relay.
   DRM stays a documented `501`, not a TODO to circumvent.
