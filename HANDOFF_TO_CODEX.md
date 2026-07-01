# Chad → Codex: complete hand-off (start here)

Everything to put the **full Chad** on the live site. All additive — nothing here overwrites your
`Hancock_Marketing_Studio.html` or `data/*.json`. Read order: this file → `CHAD_GO_LIVE.md`.

## TL;DR
1. Deploy the **brain** (`../Hancock_CoPilot/chad_server.py`) as a 2nd Render service.
2. Serve the front-end pieces (in THIS folder) and add a 2-line embed to the studio page.
3. Wire the "Ask Chad" button + a Chad tab to it.
Then Chad is live: voiced (Eric), self-learning, photo-reviewing, graphic-making, on-doctrine,
governed — floating page-to-page + a tab.

## The pieces

### Brain service — deploy from `../Hancock_CoPilot/` (keep these together)
| File | Role |
|---|---|
| `chad_server.py` | The brain/API (stdlib, binds `$PORT`). The 2nd Render service. |
| `chad_doctrine.md` | **Ryan's playbook = Chad's brain.** `chad_server.py` loads it at startup. **Deploy in the same folder.** Edit it to update what Chad knows — no code change. |
| `chad_bot.py` | Python kit for bots to join the hub. |
| `learnbot.py` | Self-learning researcher (run `--loop 12` on the host to keep Chad learning). |
| `README.md` | Full API reference. |

Env vars on the brain service: `ANTHROPIC_API_KEY` (rotated), `ELEVENLABS_API_KEY`,
`CHAD_ALLOWED_ORIGIN=https://hancock-live-marketing-studio.onrender.com`.

### Front-end — already in THIS folder (serve as static + embed)
| File | Role |
|---|---|
| `chad-widget.js` | Floating JARVIS Chad (voice + chat). 2-line embed on every page. |
| `chad-graphics.html` | On-brand graphic maker (1080² social cards). Link as a Studio tool. |

### Docs (the how-to)
- `CHAD_GO_LIVE.md` — the ordered 8-step checklist (do this).
- `CHAD_STUDIO_WIRING.md` — per-step detail incl. the governed **site-update** flow.
- `../CHAD_INTEGRATION.md` — brain deploy detail.
- `../STUDIO_CONTRACT.md` — who-owns-what (you own the HTML, radar.py owns `data/*.json`).
- `../Chad_Live_Deploy_Checklist.md` — post-deploy "is it working + secure" checklist.

## What Chad can do once live
Greets each logged-in user by name · briefs the team · remembers facts · **self-learns** the
claims/inspection/insurance/roofing world + competitors · **reviews photos** and writes content from
them (`/vision`) · **makes on-brand graphics** · **runs the studio** (governed, undo) · helps stage
**site updates** (draft → human approve → apply) · speaks (Eric) with a JARVIS orb · all on Ryan's
doctrine. Keys server-side; bots prep, humans approve; no money.

## Only Ryan can do these (real blockers)
1. **Rotate** the Anthropic key (pasted in chat once) → give the fresh one to Codex for Render env.
2. Confirm Codex has **deploy/repo access**.
