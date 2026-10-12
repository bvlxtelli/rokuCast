# CREDITS — rokuCast attributions

Every project, spec, doc or snippet reused or referenced by rokuCast **must** be
listed here. License: rokuCast itself is **AGPL-3.0-or-later** (network clause
§13 applies to the bridge).

## Logic / idea sources

| Project | Author(s) | License | What we use |
|---|---|---|---|
| [MiracleCast](https://github.com/albfan/miraclecast) | David Herrmann, Alberto Fanjul + contributors | **LGPL-2.1** (see `COPYING` upstream) | Wi-Fi Display sink pattern + WFD/RTSP M1–M7 handshake idea (`MiracleTranslator` in `src/rokucast/media.py`) — no MiracleCast code vendored |
| [Roku BrightScript reference](https://developer.roku.com/dev/docs/brightscript-language-reference) | Roku | Proprietary docs | SceneGraph receiver design (`roku-channel/`): Scene + Video node + Task polling |
| [Roku ECP](https://developer.roku.com/docs/developer-program/debugging/external-control-api.md) | Roku | Proprietary docs | `POST /launch` + `keypress` control plane (`src/rokucast/ecp.py`) |
| [DIAL (Discovery And Launch)](https://www.dial-multiscreen.org/) | Netflix/Google (DIAL multiscreen org) | Spec, royalty-free | SSDP `M-SEARCH` + `device-desc.xml` + `/apps/*` discovery emulation (`src/rokucast/server.py`, `src/rokucast/discovery.py`) |

## Libraries bundled as dependencies

- `zeroconf` (LGPL-2.1, optional `mdns` extra) — mDNS `_googlecast._tcp` announcement; everything else is stdlib — see `docs/THIRD_PARTY.md`.

## Rule

**Anything new used inside rokuCast gets a row here + `docs/THIRD_PARTY.md` before merge.**
