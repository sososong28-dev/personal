# Profile Site

Standalone source repository for He Jiansong's private and public personal website.

## Entry points

- Public profile: `/profile`
- Private login: `/me/login`
- Private archive: `/me/`
- Course landing page: `docs/商业教程-课程落地页.html`

## Brand baseline

- Brand foundation: `docs/brand/BRAND-FOUNDATION.md`
- Mood and imagery: `docs/brand/mood.md`
- Voice and copy: `docs/brand/voice.md`
- Visual tokens: `docs/brand/tokens.md`

Update the baseline before making material changes to public positioning, visual language or tone of voice.

## Local development

```powershell
cd C:\Users\Administrator\Documents\profile-site
npm install
npm run build
$env:PROFILE_SECRET_KEY = [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5001/profile` after the Flask application starts.

For the standalone course landing page:

```powershell
python -m http.server 4311 --directory .\docs
```

## Repository boundary

Tracked source includes Flask, React, static assets, deployment configuration and publishable documentation.

Never commit `.env`, `data/`, `logs/`, `node_modules/`, `.venv/`, or locally generated deployment archives. The existing `.gitignore` enforces this boundary.

## Production deployment

Production remains deployed under `/var/www/profile-site` with the `profile-site` systemd service. Build the frontend with `npm run build` before packaging a deployment release.
