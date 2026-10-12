# THIRD_PARTY — licenses of everything rokuCast depends on or calls

rokuCast itself: **AGPL-3.0-or-later** (`LICENSE`).

| Component | License (verify SPDX at release) | Notes |
|---|---|---|
| MiracleCast WFD/sink logic idea | LGPL-2.1 (upstream) | Idea/mapping only, no vendored code |
| Roku BrightScript/ECP/DIAL docs | Proprietary docs (Roku / DIAL org) | Protocol behavior reimplemented from docs |
| `zeroconf` (optional `mdns` extra) | LGPL-2.1 | mDNS `_googlecast._tcp` announcement |
| Python stdlib (`http.server`, `urllib`, `socket`) | PSF-2.0 | HTTP + SSDP + ECP, no extra deps |
| `pytest`, `ruff` | MIT | Dev-only |
| Roku OS (Video node, ECP, Screen Mirroring) | Proprietary (Roku) | Receiver platform + native Miracast sink |

**Rule: new dependency → row here + `docs/CREDITS.md` before merge.**
