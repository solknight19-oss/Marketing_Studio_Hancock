# ION Training Deployment

Production domain:

`ion-training.hancockclaims.com`

Render service URL:

`https://hancock-ion-training.onrender.com`

## What this is

This folder is a static training site. It does not need a backend, database, API keys, or server-side code.

## Files to publish

Publish the entire `ION_Guide_Walkthrough` folder:

- `index.html`
- `styles.css`
- `script.js`
- `assets/`
- `CNAME`
- `netlify.toml` if using Netlify
- `vercel.json` if using Vercel

## Recommended launch path

1. Deploy the `hancock-ion-training` Render service from this folder.
2. Confirm `https://hancock-ion-training.onrender.com` opens the training site.
3. Add the custom domain `ion-training.hancockclaims.com` to that Render service.
4. In DNS for `hancockclaims.com`, add the CNAME record requested by Render.
5. Enable HTTPS/SSL in the Render dashboard.
6. Open `https://ion-training.hancockclaims.com` on desktop and phone.

## DNS note

The final CNAME target depends on the hosting provider. Examples:

- Netlify usually asks for a CNAME to the Netlify site hostname.
- Vercel usually asks for a CNAME to `cname.vercel-dns.com`.
- GitHub Pages usually asks for a CNAME to the GitHub Pages hostname.
- Cloudflare Pages usually asks for a CNAME to the Pages hostname.

Use the exact DNS target shown by the chosen host.

## Final QA

- Confirm the left navigation labels match the ION app categories.
- Confirm all screenshots load.
- Confirm the ChatGPT helper content appears under the Plumbing/HVAC flow.
- Confirm the site works on a phone-sized screen.
