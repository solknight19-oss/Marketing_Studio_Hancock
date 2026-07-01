# Wiring the real Chad into the live Studio (for Codex)

The studio already has Chad hooks (`HancockLive.openChad()`, the "Ask Chad" buttons, the tab nav). They just aren't connected to a real brain yet — `server.py` has no Claude/ElevenLabs, so Chad can't think or talk. This connects them to the brain Claude built, giving Chad **real voice (ElevenLabs), smart chat (Claude), memory, the bot crew, and the floating JARVIS orb** — page to page, plus a Chad tab.

## Step 1 — Deploy Chad's brain (once)
Deploy `chad_server.py` (from `Hancock_CoPilot/`) as a **second Render web service**. It's pure stdlib, binds `$PORT`, no deps. Full details in `../CHAD_INTEGRATION.md`. Set env on that service:
- `ANTHROPIC_API_KEY` (rotated key) · `ELEVENLABS_API_KEY` · `CHAD_ALLOWED_ORIGIN=https://hancock-live-marketing-studio.onrender.com`

Call the brain's public URL `BRAIN_URL` below.

## Step 2 — Add the floating Chad to the studio (one include)
`chad-widget.js` is already in this folder. Add to the studio page, right before `</body>`:
```html
<script>window.CHAD_CONFIG = { apiBase: "BRAIN_URL", user: CURRENT_USER };</script>
<script src="chad-widget.js"></script>
```
- `CURRENT_USER` = the logged-in person's name (you already know it server-side — inject it: `"Ryan"`, `"Cassie"`, or `"Jennifer"`). That makes greetings + briefings personal.
- This gives the **floating JARVIS orb bottom-right on every page** → click to talk, with real voice. Serve `chad-widget.js` as a static file.

## Step 3 — Point your existing "Ask Chad" at it
Replace the body of `HancockLive.openChad()` with one line so your existing buttons open the real Chad:
```js
openChad: function(){ if (window.ChadWidget) ChadWidget.open(); }
```

## Step 4 — Add a "Chad" tab (optional but nice)
Add a tab to `#tabs` and a view that hosts the briefing. Simplest: the tab's button calls `ChadWidget.open()`. Or render a dedicated panel that pulls `GET BRAIN_URL/briefing?user=CURRENT_USER` and shows the team briefing + next steps inline.

## What the brain gives you (so the studio's own bots plug in too)
Endpoints (full list in `Hancock_CoPilot/README.md`): `/chat`, `/speak`, `/briefing`, `/memory`, `/bots` + `/bots/register`, `/knowledge`, `/prep` + `/prep/approve`, `/tasks` + `/tasks/done`, `/action` (governed), `/audit`, `/permissions`.
Point `bot_council.py` / `marketing_bot.py` at `/bots/register` + `/prep` so they show in Chad's crew and their work flows into the prep queue.

## Studio data contract (already agreed — see ../STUDIO_CONTRACT.md)
Codex owns `Hancock_Marketing_Studio.html`; radar.py owns `data/*.json` (refresh via `radar.py --data-only`; Chad's `run_studio` already does this). No file collisions.

## Step 5 — Let Chad help make site updates (governed)
Cassie/Jennifer can ask Chad to change the site. Chad **drafts + stages** the change; a human **approves**; the site **applies** it. No autonomous production rewrites.

- **Stage:** Chad posts the request to the brain's prep queue with `kind:"site_update"` (title = what to change, body = the proposed new content/copy). It sits `pending`.
- **Approve:** a human approves in Chad's panel (`POST /prep/approve {id}`) — same governance as everything else; audited + reversible.
- **Apply (your side):** poll `GET /prep?status=approved` for items where `kind==="site_update"` and apply them:
  - **Content/copy that's data-driven** (hero text, blurbs, library, settings) → write to your content/data store; the page re-renders. Safe + reversible.
  - **Code/layout/structure changes** → surface them as a to-do for a human to implement in the repo + redeploy. Chad never edits production code directly.
- Keep the hard line: publishing externally (CMS/LinkedIn/email), deleting, or spending stays human-approved; money never.

This reuses the existing prep→approve flow — no new brain endpoints needed; you just consume approved `site_update` items.

## Net result
- Chad floats in the corner on every studio page (JARVIS-blue orb, voice = "Eric").
- Your "Ask Chad" buttons + a Chad tab all open the same real Chad.
- He greets each logged-in user by name, briefs them, remembers facts, and can run the studio (governed, with undo).
- Keys stay server-side; bots prep, humans approve; no money — all unchanged.
