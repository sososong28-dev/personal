# Profile Site

何坚松（Nelson）的个人网站：一个可公开访问的职业主页，以及一个经登录保护的私密项目档案。

## 入口与访问边界

| Surface | Path | Access |
| --- | --- | --- |
| Public profile | `/profile` | Public, indexable |
| Private login | `/me/login` | Public login form |
| Private archive | `/me/` | Authenticated users only |
| Course landing page | `docs/商业教程-课程落地页.html` | Static file |

The public profile exposes only redacted positioning, capability and selected result summaries. Private project material remains behind the `/me` login boundary.

## Stack

- Python / Flask for routing, session authentication and public-profile SEO endpoints
- React + TypeScript + Vite for the private archive UI
- Static assets under `static/` and generated frontend bundle under `dist/`
- SQLite for local private-user initialization and session-related data (not tracked)

## Local development

Prerequisites: Python 3.10+ and Node.js 20+.

```powershell
cd C:\Users\Administrator\Documents\profile-site
npm install
npm run build
$env:PROFILE_SECRET_KEY = [guid]::NewGuid().ToString('N')
$env:PROFILE_ADMIN_PASSWORD = 'set-a-local-development-password'
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5001/profile` for the public page or `http://127.0.0.1:5001/me/login` for the private archive.

## Environment variables

Copy `.env.example` for a local or production environment; do not commit a populated `.env` file.

| Name | Required | Purpose |
| --- | --- | --- |
| `PROFILE_SECRET_KEY` | Yes in production | Signs Flask sessions. Use a random, stable secret. |
| `PROFILE_ADMIN_USERNAME` | No | Initial admin username; defaults to `sososong`. |
| `PROFILE_ADMIN_PASSWORD` | Yes | Initial admin password when the user does not yet exist in SQLite. |
| `PORT` | No | Flask development port; defaults to `5001`. |

Changing `PROFILE_ADMIN_PASSWORD` does not update a user that already exists in `data/profile.db`.

## Build and validation

```powershell
npm run build
.\.venv\Scripts\python.exe -m py_compile app.py wsgi.py
```

`dist/` is deliberately versioned because the Flask app serves the prebuilt frontend bundle in production.

## Deployment

Deploy the tracked project to `/var/www/profile-site`, install Python dependencies, run `npm ci` and `npm run build`, then restart the `profile-site` systemd service. The exact handoff checklist, Nginx routing rules and rollback instructions are in [HANDOFF.md](HANDOFF.md).

## Repository boundary

Never commit runtime state or credentials: `.env`, `data/`, `logs/`, `uploads/`, `.venv/`, `node_modules/`, or `.deploy/`. The latter contains local deployment archives and UI screenshots only.

## Brand and course materials

- Brand baseline: [`docs/brand/BRAND-FOUNDATION.md`](docs/brand/BRAND-FOUNDATION.md)
- Brand voice: [`docs/brand/voice.md`](docs/brand/voice.md)
- Course package: [`docs/商业教程-课程包README.md`](docs/商业教程-课程包README.md)

Update the brand baseline before making material changes to public positioning, visual language, or tone of voice.
