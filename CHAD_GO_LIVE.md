# Chad → Go Live: master checklist (for Codex)

This is the one ordered list to put the **full Chad** on the live site. Each step links to a detailed doc. Nothing here overwrites your `Hancock_Marketing_Studio.html` — it's all additive + config.

Brain source files live in `../Hancock_CoPilot/`. Front-end pieces are already copied into THIS folder (`chad-widget.js`, `chad-graphics.html`).

---

## 1. Deploy Chad's brain (2nd Render service)  → details: ../CHAD_INTEGRATION.md
- New Render web service from **`../Hancock_CoPilot/chad_server.py`** (pure stdlib, binds `$PORT`, no requirements).
- Start command: `python3 chad_server.py`
- Env vars on that service:
  - `ANTHROPIC_API_KEY` = the **rotated** key (smart chat, research, vision)
  - `ELEVENLABS_API_KEY` = voice (Eric)
  - `CHAD_ALLOWED_ORIGIN` = `https://hancock-live-marketing-studio.onrender.com`
- Note the brain's public URL → call it `BRAIN_URL`.
- Health: `GET BRAIN_URL/health` should return `{ok:true, ai:true, voice:true}`.

## 2. Float Chad on every page  → details: CHAD_STUDIO_WIRING.md (steps 2-3)
- Serve `chad-widget.js` (in this folder) as a static asset.
- Add before `</body>` of the studio page template:
  ```html
  <script>window.CHAD_CONFIG = { apiBase: "BRAIN_URL", user: CURRENT_USER };</script>
  <script src="chad-widget.js"></script>
  ```
  `CURRENT_USER` = the logged-in person's name (inject server-side).
- Point your existing buttons at it: `openChad: function(){ if(window.ChadWidget) ChadWidget.open(); }`

## 3. Add a "Chad" tab
- New tab in `#tabs`; its view calls `ChadWidget.open()` (or render the briefing inline from `BRAIN_URL/briefing?user=CURRENT_USER`).

## 4. Wire the new powers (all on the brain already)
- **Photo review:** add an "Analyze a photo" control → file → `POST BRAIN_URL/vision {user, image:<dataURL>, prompt}` → show the reply. (Chad analyzes inspection photos + drafts content.)
- **Graphic maker:** link/serve `chad-graphics.html` as a Studio tool (on-brand 1080² social cards; uses `/chat` for headlines).

## 5. Site updates (governed)  → details: CHAD_STUDIO_WIRING.md (step 5)
- Poll `GET BRAIN_URL/prep?status=approved` for `kind=="site_update"` → apply data-driven content automatically; flag code/layout changes for a human. Approvals already happen in Chad's panel.

## 6. Connect the bots to the hub
- Have `bot_council.py` / `marketing_bot.py` (and `../Hancock_CoPilot/learnbot.py`) register + prep via the hub (`/bots/register`, `/prep`, `/knowledge`) so they appear in Chad's crew and their work flows into the review queue. Kit: `../Hancock_CoPilot/chad_bot.py` (Python) / `chad-widget.js` patterns (JS). Endpoints: `../Hancock_CoPilot/README.md`.
- Optional: schedule `learnbot.py --loop 12` on the host so Chad keeps self-learning the industry + competitors.

## 7. Studio data contract  → details: ../STUDIO_CONTRACT.md
- You own `Hancock_Marketing_Studio.html`; radar.py owns `data/*.json` (refresh via `radar.py --data-only`; Chad's `run_studio` action already does this). Don't write the data; I won't write your page.

## 8. Security pass  → details: ../Chad_Live_Deploy_Checklist.md (section ②)
- Both keys in **Render env**, never in the repo. Repo **private**. **CORS** locked (step 1). Confirm the login gate blocks the new `/vision`-style calls too (gate the routes, not just the page). **Rotate** the Anthropic key that was pasted in chat.

---

## Net result
Floating JARVIS Chad on every page + a Chad tab + "Ask Chad" buttons — all the **real** Chad: greets each user by name, briefs them, remembers, self-learns the industry & competitors, reviews photos, makes on-brand graphics, runs the studio, and helps stage governed site updates. Voice = Eric. Keys server-side. Humans approve anything consequential; no money.
