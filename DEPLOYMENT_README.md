# Hancock Live Marketing Studio - Deployment Package

This folder is the deployable site package for the next phase.

Included:
- Email-based login for Ryan, Cassie, and Jennifer
- Secure admin invitations and one-time password setup/reset links
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

Local-only bootstrap logins are written to `app_data/INITIAL_LOGINS.md` on first run.

## Deploy on Render

1. Put this folder in a GitHub repo as the repo root.
2. Create a Render Blueprint/Web Service from `render.yaml`.
3. Set `ANTHROPIC_API_KEY` privately if you want AI drafting.
4. Keep the persistent disk mounted at `/var/data` so logins, tasks, sessions, and drafts survive deploys.
5. Set `RESEND_API_KEY` privately for invitations and password-reset email.
6. Verify `hancockclaims.com` in Resend and set `EMAIL_FROM` to an address on that verified domain.
7. Set `ADMIN_PASSWORD` once as Ryan's bootstrap password. After Ryan signs in, he can invite the team from Admin. Do not set Cassie or Jennifer passwords; they create their own.

## Production hardening

Security included:
- Passwords stored only as salted PBKDF2 hashes
- One-time, hashed setup and reset tokens
- 24-hour invitation expiry and one-hour reset expiry
- Hancock-domain restriction and request rate limiting
- Secure, HTTP-only production session cookies

Before broader use:
- Add managed backups for `/var/data/studio.db`.
- Move to Postgres if usage grows.
- Keep API keys only in environment variables.
- Add admin user-management UI.
- Add paid voice layer: OpenAI Realtime or ElevenLabs Conversational AI.
