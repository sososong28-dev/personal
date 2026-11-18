# Profile Site Handoff

## Current delivery

This repository contains the current public profile at `/profile`, the authenticated private archive at `/me/`, the React source for the archive, its production `dist/` bundle, static project media, brand guidance, and the course landing-page package.

The live host uses a Flask application behind Nginx. Private content must remain protected by the `/me` login flow; do not expose the archive directly as a static site.

## Production layout

```text
/var/www/profile-site
├── app.py
├── wsgi.py
├── gunicorn.conf.py
├── requirements.txt
├── package.json
├── dist/
├── static/
├── .env                 # server-only, never committed
├── data/                # server-only SQLite state
└── logs/                # server-only logs
```

Systemd service: `profile-site`.

## Deploy checklist

1. Fetch the intended Git revision into `/var/www/profile-site`.
2. Ensure `.env` is present with a strong `PROFILE_SECRET_KEY` and `PROFILE_ADMIN_PASSWORD`.
3. Update Python dependencies: `.venv/bin/pip install -r requirements.txt`.
4. Build the archive UI: `npm ci && npm run build`.
5. Restart: `sudo systemctl restart profile-site`.
6. Validate the public endpoint, private login redirect, and asset responses.

```bash
cd /var/www/profile-site
git pull --ff-only origin main
.venv/bin/pip install -r requirements.txt
npm ci
npm run build
sudo systemctl restart profile-site
curl -I https://<host>/profile
curl -I https://<host>/me/
```

Expected behavior:

- `/profile` returns `200`, permits indexing, and includes a canonical URL.
- `/robots.txt` permits `/profile` and disallows `/me`.
- `/sitemap.xml` lists `/profile`.
- An unauthenticated request to `/me/` redirects to `/me/login`.
- `/profile-assets/*` is public; `/me/assets/*` requires authentication.

## Nginx requirements

Do not strip the `/me` prefix. The proxy needs to preserve the original host and forwarding headers; the application uses the request host when generating public canonical, sitemap, and asset URLs.

```nginx
location = /me { return 301 /me/; }

location / {
    proxy_pass http://127.0.0.1:5001;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Run `nginx -t` before reloading Nginx.

## Operational notes

- The first application startup initializes the admin user only when it is absent from `data/profile.db`.
- A later environment-password change does not reset an existing account. Reset it explicitly in the database when needed.
- Keep `data/`, `logs/`, uploaded files, local release archives, and `.env` outside Git.
- `dist/` is tracked to keep the checked-out release runnable, but rebuild it whenever `src/` or frontend dependencies change.

## Rollback

Use the last known-good Git commit, rebuild the frontend, then restart the service:

```bash
cd /var/www/profile-site
git log --oneline -10
git checkout <known-good-commit>
npm ci && npm run build
sudo systemctl restart profile-site
```

After recovery, validate both `/profile` and the `/me/login` → `/me/` flow before declaring the rollback complete.
