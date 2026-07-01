# Deploy Next Steps - Hancock Live Site

Current status: the deployment package is ready and committed locally.

Local repo:
`/Users/rknight/Desktop/Knight/Hancock_Live_Site_Deploy`

Clean upload ZIP:
`/Users/rknight/Desktop/Knight/Hancock_Live_Site_Deploy_CLEAN.zip`

## Blocker

The GitHub token provided was valid enough to reach GitHub, but it does not have permission to create/access repositories. GitHub returned: `Resource not accessible by personal access token`.

## Fastest path

1. In GitHub, create a new private repository named:
   `hancock-live-marketing-studio`

2. Create a fine-grained token for that repository with:
   - Repository access: the new repo
   - Contents: Read and write
   - Metadata: Read

3. Give Codex the repository URL, not the password/token if you prefer. If you provide a token, revoke/rotate it after deployment.

4. Codex can then run:
   - add remote
   - push `main`

5. In Render:
   - New Blueprint/Web Service from GitHub repo
   - Use `render.yaml`
   - Add private env var `ANTHROPIC_API_KEY` when ready
   - Keep persistent disk `/var/data`

## Render settings if creating manually

- Runtime: Docker
- Health check path: `/healthz`
- Persistent disk: `/var/data`, 1 GB
- Environment variables:
  - `APP_DATA_DIR=/var/data`
  - `HOST=0.0.0.0`
  - `SESSION_SECRET=<random long value>`
  - `ANTHROPIC_API_KEY=<optional>`

## After first deploy

Initial user passwords are generated in `/var/data/INITIAL_LOGINS.md`. Change them before real use.
