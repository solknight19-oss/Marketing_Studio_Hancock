# Hancock Live Marketing Studio - Deployment Package

This folder is the deployable site package for the next phase.

Included:
- Login-gated shared workspace for Ryan, Cassie, and Jennifer
- Shared drafts and task board
- Chad guidance connected to the bot council
- Live industry scan action using `marketing_bot.py`
- Approved Marketing Studio at `/studio`
- Chad feed endpoint at `/api/chad-feed`
- Health check at `/healthz`

## Local preview

```bash
cd Hancock_Live_Site_Deploy
python3 server.py
```

Open `http://127.0.0.1:8765`.

Initial generated logins are written to `app_data/INITIAL_LOGINS.md` on first run.

## Deploy on Render

1. Put this folder in a GitHub repo as the repo root.
2. Create a Render Blueprint/Web Service from `render.yaml`.
3. Set `ANTHROPIC_API_KEY` privately if you want AI drafting.
4. Keep the persistent disk mounted at `/var/data` so logins, tasks, sessions, and drafts survive deploys.
5. Set `ADMIN_PASSWORD`, `CASSIE_PASSWORD`, and `JENNIFER_PASSWORD` in Render. These values reset the matching login whenever the service starts.

## Production hardening

Before broad use:
- Add email invites/password reset.
- Add managed backups for `/var/data/studio.db`.
- Move to Postgres if usage grows.
- Keep API keys only in environment variables.
- Add admin user-management UI.
- Add paid voice layer: OpenAI Realtime or ElevenLabs Conversational AI.
