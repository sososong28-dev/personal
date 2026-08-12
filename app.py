from __future__ import annotations

import os
import sqlite3
import mimetypes
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "profile.db"
FRONTEND_DIST = BASE_DIR / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

ADMIN_USERNAME = os.getenv("PROFILE_ADMIN_USERNAME", "sososong")
ADMIN_PASSWORD = os.getenv("PROFILE_ADMIN_PASSWORD", "")
SECRET_KEY = os.getenv("PROFILE_SECRET_KEY", "profile-site-change-me")
URL_PREFIX = "/me"

mimetypes.add_type("image/webp", ".webp")


def create_app() -> Flask:
    app = Flask(__name__, static_url_path=f"{URL_PREFIX}/static")
    app.secret_key = SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
    app.config["SESSION_COOKIE_NAME"] = "me_session"
    app.config["SESSION_COOKIE_PATH"] = URL_PREFIX
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    init_db()

    @app.after_request
    def add_private_headers(response):
        if request.path == URL_PREFIX or request.path.startswith(f"{URL_PREFIX}/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    @app.route("/")
    def root():
        return redirect(f"{URL_PREFIX}/")

    @app.route("/profile")
    @app.route("/profile/")
    def public_profile():
        response = app.make_response(
            render_template_string(PUBLIC_PROFILE_TEMPLATE, base_url=request.host_url.rstrip("/"))
        )
        response.headers["Cache-Control"] = "public, max-age=300"
        response.headers["X-Robots-Tag"] = "index, follow"
        return response

    @app.route("/profile-assets/<path:filename>")
    def profile_assets(filename):
        response = send_from_directory(BASE_DIR / "static", filename)
        response.headers["Cache-Control"] = "public, max-age=2592000, immutable"
        return response

    @app.route("/robots.txt")
    def robots_txt():
        base_url = request.host_url.rstrip("/")
        body = "\n".join(
            [
                "User-agent: *",
                "Allow: /profile",
                "Allow: /sitemap.xml",
                "Disallow: /me",
                f"Sitemap: {base_url}/sitemap.xml",
                "",
            ]
        )
        response = app.response_class(body, mimetype="text/plain")
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response

    @app.route("/sitemap.xml")
    def sitemap_xml():
        base_url = request.host_url.rstrip("/")
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/profile</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
        response = app.response_class(body, mimetype="application/xml")
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response

    @app.route(f"{URL_PREFIX}/")
    def home():
        if not is_logged_in():
            return redirect(f"{URL_PREFIX}/login?next={URL_PREFIX}/")
        return frontend_index()

    @app.route(f"{URL_PREFIX}/assets/<path:filename>")
    def frontend_assets(filename):
        if not is_logged_in():
            return redirect(f"{URL_PREFIX}/login?next={URL_PREFIX}/")
        return send_from_directory(FRONTEND_DIST / "assets", filename)

    @app.route(f"{URL_PREFIX}/projects/yikougege")
    def yikougege_project():
        if not is_logged_in():
            return redirect(f"{URL_PREFIX}/login?next={URL_PREFIX}/projects/yikougege")
        return frontend_index()

    @app.route(f"{URL_PREFIX}/projects/kefumei")
    def kefumei_project():
        if not is_logged_in():
            return redirect(f"{URL_PREFIX}/login?next={URL_PREFIX}/projects/kefumei")
        return frontend_index()

    @app.route(f"{URL_PREFIX}/login", methods=["GET", "POST"])
    def login():
        next_path = safe_next(request.values.get("next"), f"{URL_PREFIX}/")
        if request.method == "GET" and is_logged_in():
            return redirect(next_path)

        error = ""
        username = ""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = authenticate(username, password)
            if user:
                session.clear()
                session.permanent = True
                session["logged_in"] = True
                session["username"] = user["username"]
                session["role"] = user["role"]
                record_login(user["id"], client_ip())
                return redirect(next_path)
            error = "账号或密码错误。"

        return render_template_string(LOGIN_TEMPLATE, error=error, username=username, next_path=next_path)

    @app.route(f"{URL_PREFIX}/logout")
    def logout():
        session.clear()
        return redirect(f"{URL_PREFIX}/login")

    @app.route(f"{URL_PREFIX}/<path:frontend_path>")
    def frontend_route(frontend_path: str):
        if not is_logged_in():
            return redirect(f"{URL_PREFIX}/login?next={request.path}")
        return frontend_index()

    return app


def frontend_index():
    if FRONTEND_INDEX.exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return render_template_string(HOME_TEMPLATE, username=session.get("username", ""))


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                enabled INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT NOT NULL DEFAULT '',
                last_login_ip TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        row = conn.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()
        if not row:
            if not ADMIN_PASSWORD:
                raise RuntimeError("PROFILE_ADMIN_PASSWORD must be set before first startup.")
            conn.execute(
                "INSERT INTO users (username, password_hash, role, enabled) VALUES (?, ?, 'admin', 1)",
                (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)),
            )
        conn.commit()


def authenticate(username: str, password: str) -> dict[str, str] | None:
    if not username or not password:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, enabled FROM users WHERE lower(username) = lower(?)",
            (username,),
        ).fetchone()
    if not row or not row["enabled"]:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return {"id": str(row["id"]), "username": row["username"], "role": row["role"]}


def record_login(user_id: str, ip: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP, last_login_ip = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ip, user_id),
        )
        conn.commit()


def is_logged_in() -> bool:
    return session.get("logged_in") is True


def safe_next(value: str | None, default: str) -> str:
    path = str(value or "").strip()
    if not path or not path.startswith("/") or path.startswith("//") or "://" in path:
        return default
    if not path.startswith(f"{URL_PREFIX}/") and path != URL_PREFIX:
        return default
    return path


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.remote_addr or ""


PUBLIC_PROFILE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>何坚松 Nelson｜AI × Consumer Product</title>
  <meta name="description" content="何坚松 Nelson｜AI + C端消费者产品负责人 / 产品总监公开主页，聚焦 AI 消费者产品、产品企划、GTM 与商品经营。" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{{ base_url }}/profile" />
  <meta property="og:title" content="何坚松 Nelson｜AI × Consumer Product" />
  <meta property="og:description" content="面向企业高管和投资者的公开能力展示：AI 消费者产品、产品企划、GTM、商品经营与品牌增长。" />
  <meta property="og:type" content="profile" />
  <meta property="og:url" content="{{ base_url }}/profile" />
  <meta property="og:image" content="{{ base_url }}/profile-assets/nelson-hero-character.png" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "何坚松",
    "alternateName": "Kinsong Ho",
    "url": "{{ base_url }}/profile",
    "email": ["mailto:kinsongho@qq.com", "mailto:sososong28@gmail.com"],
    "jobTitle": "AI 与 C 端消费者产品负责人 / 产品总监",
    "knowsAbout": ["AI 消费者产品", "C 端 AI 应用", "智能硬件", "产品企划", "GTM", "商品经营", "消费者洞察", "品牌增长"]
  }
  </script>
  <style>
    :root {
      --brand-ink: #0c0c0c;
      --brand-ink-raised: #171615;
      --brand-paper: #f4f1ea;
      --brand-paper-raised: #fffdf8;
      --brand-signal: #ff2442;
      --brand-text-dark: #f4f1ea;
      --brand-muted-dark: rgba(244, 241, 234, .66);
      --brand-text-light: #171615;
      --brand-muted-light: #625e57;
      --brand-line-dark: rgba(244, 241, 234, .14);
      --brand-line-light: rgba(23, 22, 21, .12);
      --radius-control: 12px;
      --radius-card: 16px;
      --radius-media: 20px;
      --section-space: 96px;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { margin: 0; color: var(--brand-text-dark); background: var(--brand-ink); font-family: "Noto Sans SC", "Microsoft YaHei", Arial, sans-serif; line-height: 1.65; overflow-x: hidden; }
    h1, h2, h3, p { text-wrap: pretty; }
    a { color: inherit; text-decoration: none; }
    .page { min-height: 100vh; }
    .nav { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 18px clamp(20px, 5vw, 72px); background: rgba(12, 12, 12, .78); border-bottom: 1px solid rgba(255, 255, 255, .08); backdrop-filter: blur(18px); }
    .brand { display: inline-flex; gap: 5px; font-weight: 900; letter-spacing: .02em; }
    .nav-links { display: flex; align-items: center; gap: 16px; font-size: 14px; color: rgba(255, 255, 255, .64); }
    .nav-links a:hover { color: #fff; }
    .login-link { border: 1px solid rgba(255, 255, 255, .16); border-radius: 999px; padding: 8px 13px; color: rgba(255, 255, 255, .84); background: rgba(255, 255, 255, .04); }
    .mobile-menu { display: none; }
    .hero { position: relative; display: grid; grid-template-columns: minmax(0, .95fr) minmax(360px, .78fr); gap: clamp(36px, 5vw, 72px); align-items: center; min-height: calc(100vh - 74px); padding: clamp(48px, 8vw, 96px) max(clamp(20px, 6vw, 88px), calc((100vw - 1280px) / 2)) 42px; border-bottom: 1px solid rgba(255, 255, 255, .08); background: linear-gradient(115deg, #0c0c0c 0%, #15120f 48%, #0c0c0c 100%); }
    .hero::before { content: ""; position: absolute; inset: 0 0 auto; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.35), transparent); }
    .eyebrow { display: inline-flex; margin: 0 0 22px; border: 1px solid rgba(255, 255, 255, .1); border-radius: 999px; background: rgba(255, 255, 255, .04); padding: 8px 14px; color: rgba(255, 255, 255, .64); font-size: 12px; font-weight: 900; letter-spacing: .18em; text-transform: uppercase; }
    .hero-name { max-width: 880px; margin: 0; color: var(--brand-paper); font-family: "Arial Black", "Arial Narrow", Arial, sans-serif; font-size: clamp(76px, 13vw, 188px); line-height: .82; letter-spacing: -.045em; text-transform: uppercase; font-weight: 900; }
    .hero-chinese { margin: 22px 0 0; font-size: clamp(38px, 6vw, 88px); line-height: .92; letter-spacing: 0; color: #fff; font-weight: 850; }
    .hero-copy { max-width: 760px; margin: 30px 0 0; color: rgba(255, 255, 255, .72); font-size: clamp(18px, 2.1vw, 24px); font-weight: 650; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
    .button { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 0 18px; border-radius: var(--radius-control); border: 1px solid rgba(255, 255, 255, .14); background: var(--brand-signal); color: #fff; font-weight: 800; }
    .button.secondary { background: transparent; color: rgba(255,255,255,.82); }
    .hero-text-link { display: inline-flex; align-items: center; min-height: 44px; padding: 0 4px; color: rgba(255,255,255,.72); font-weight: 700; }
    .hero-text-link::after { content: "↗"; margin-left: 7px; color: var(--brand-signal); }
    .hero-text-link:hover { color: #fff; }
    .secondary-actions { margin-top: 12px; }
    .hero-meta { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; color: rgba(255,255,255,.62); font-size: 13px; font-weight: 700; }
    .hero-meta span { border: 1px solid rgba(255,255,255,.1); border-radius: 999px; background: rgba(255,255,255,.035); padding: 7px 10px; }
    .focus-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; max-width: 620px; }
    .focus-row span { border-radius: 999px; background: rgba(255,36,66,.14); color: rgba(255,255,255,.82); padding: 7px 10px; font-size: 12px; font-weight: 800; }
    .visual { position: relative; min-height: 620px; border-left: 1px solid rgba(255, 255, 255, .08); display: grid; align-items: end; padding-left: clamp(18px, 4vw, 44px); }
    .visual::before { content: ""; position: absolute; inset: 12% 4% 2%; border-radius: 999px; background: radial-gradient(circle at 50% 42%, rgba(255, 36, 66, .18), rgba(255,255,255,.06) 38%, transparent 68%); filter: blur(30px); }
    .visual img { position: relative; z-index: 2; width: min(100%, 460px); max-height: 640px; object-fit: contain; filter: drop-shadow(0 34px 70px rgba(0, 0, 0, .42)); }
    .signal { position: absolute; z-index: 3; right: 0; top: 28px; display: grid; gap: 10px; width: min(270px, 74%); }
    .signal span { display: block; padding: 10px 12px; border: 1px solid rgba(255, 255, 255, .1); border-radius: 12px; background: rgba(17, 17, 17, .78); color: rgba(255,255,255,.82); font-size: 13px; font-weight: 800; backdrop-filter: blur(12px); }
    .metrics { position: absolute; left: clamp(18px, 4vw, 44px); right: 0; bottom: 24px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; border: 1px solid rgba(255, 255, 255, .08); border-radius: 16px; background: rgba(17, 17, 17, .86); padding: 16px; backdrop-filter: blur(14px); }
    .metric { text-align: center; }
    .metric small { display: block; color: rgba(255, 255, 255, .46); font-size: 12px; font-weight: 800; }
    .metric strong { display: block; margin-top: 4px; color: #fff; font-size: clamp(18px, 2vw, 26px); line-height: 1; }
    section { padding: var(--section-space) clamp(20px, 6vw, 88px); background: var(--brand-ink); }
    .section-inner { max-width: 1280px; margin: 0 auto; }
    .section-head { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }
    h2 { margin: 0; font-size: clamp(28px, 4vw, 54px); line-height: 1.05; }
    .section-note { max-width: 520px; margin: 0; color: rgba(255, 255, 255, .58); }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
    .results-section { background: #0c0c0c; color: #fff; }
    .result-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid var(--brand-line-dark); border-radius: var(--radius-media); overflow: hidden; background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.014)); }
    .result-card { min-height: 190px; padding: 30px; border-right: 1px solid rgba(255,255,255,.1); display: flex; flex-direction: column; justify-content: space-between; }
    .result-card:last-child { border-right: 0; }
    .result-card small { color: rgba(255,255,255,.42); font-size: 11px; font-weight: 900; letter-spacing: .14em; text-transform: uppercase; }
    .result-card strong { color: #ff2442; font-size: clamp(38px, 4vw, 56px); line-height: 1; letter-spacing: 0; }
    .result-card p { margin: 14px 0 0; color: rgba(255,255,255,.68); font-size: 14px; }
    .about-section { background: var(--brand-paper); color: var(--brand-text-light); }
    .about-section .eyebrow { border-color: rgba(17,17,17,.08); background: rgba(17,17,17,.04); color: #ff2442; }
    .about-title { max-width: 920px; margin: 0; font-size: clamp(48px, 7vw, 108px); line-height: .9; letter-spacing: 0; font-weight: 1000; }
    .about-cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 46px; }
    .about-card { min-height: 260px; border: 1px solid var(--brand-line-light); border-radius: var(--radius-card); background: var(--brand-paper-raised); padding: 28px; }
    .about-card small { color: rgba(17,17,17,.42); font-size: 12px; font-weight: 900; letter-spacing: .18em; text-transform: uppercase; }
    .about-card strong { display: block; margin-top: 32px; font-size: clamp(24px, 3vw, 34px); line-height: 1.05; letter-spacing: 0; }
    .about-card p { margin: 20px 0 0; color: rgba(17,17,17,.62); }
    .timeline-section, .cap-section { background: #0c0c0c; color: #fff; }
    .timeline-layout { margin-top: 46px; border-top: 1px solid rgba(255,255,255,.16); }
    .timeline-list { display: grid; }
    .timeline-card { display: grid; grid-template-columns: 110px minmax(220px, .8fr) minmax(0, 1.45fr); gap: 26px; padding: 28px 0; border-bottom: 1px solid rgba(255,255,255,.12); background: transparent; }
    .timeline-card small { display: block; color: #ff2442; font-weight: 900; letter-spacing: .08em; }
    .timeline-card strong { display: block; color: #fff; font-size: clamp(22px, 2.4vw, 32px); line-height: 1.12; }
    .timeline-card p { margin: 0; color: rgba(255,255,255,.64); line-height: 1.8; }
    .pill-row { display: flex; flex-wrap: wrap; gap: 10px; }
    .info-pill { display: inline-flex; border: 1px solid rgba(255,255,255,.1); border-radius: 999px; background: rgba(255,255,255,.04); padding: 8px 14px; color: rgba(255,255,255,.68); font-size: 14px; font-weight: 700; }
    .detail-title { margin: 54px 0 0; font-size: clamp(48px, 6vw, 86px); line-height: .92; letter-spacing: 0; font-weight: 1000; }
    .detail-copy { max-width: 720px; margin: 28px 0 0; color: rgba(255,255,255,.68); font-size: 18px; line-height: 1.9; }
    .cap-head { display: grid; grid-template-columns: .82fr 1.18fr; gap: 28px; align-items: end; border-bottom: 1px solid rgba(255,255,255,.1); padding-bottom: 40px; }
    .cap-grid { display: grid; margin-top: 40px; border-top: 1px solid rgba(255,255,255,.16); }
    .cap-card { display: grid; grid-template-columns: 110px minmax(220px, .8fr) minmax(0, 1.45fr) auto; gap: 26px; align-items: start; padding: 28px 0; border: 0; border-bottom: 1px solid rgba(255,255,255,.12); border-radius: 0; background: transparent; }
    .cap-index { color: #ff2442; font-size: 18px; line-height: 1.2; font-weight: 1000; letter-spacing: .08em; }
    .cap-card strong { display: block; font-size: clamp(24px, 2.5vw, 34px); line-height: 1.1; letter-spacing: 0; }
    .cap-card p { margin: 0; color: rgba(255,255,255,.62); line-height: 1.85; }
    .cap-card .tag-row { margin: 0; justify-content: flex-end; max-width: 250px; }
    .projects { background: #f4f1ea; color: #111; }
    .project-layout { display: grid; gap: 18px; margin-top: 46px; }
    .project-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; border-top: 1px solid rgba(17,17,17,.14); }
    .project-tab { cursor: pointer; text-align: left; font: inherit; color: inherit; border: 0; border-bottom: 1px solid rgba(17,17,17,.14); border-radius: 0; background: transparent; padding: 20px 18px 20px 0; transition: color .2s ease, background .2s ease; }
    .project-tab + .project-tab { padding-left: 18px; border-left: 1px solid rgba(17,17,17,.14); }
    .project-tab:hover, .project-tab.is-active { color: #ff2442; box-shadow: none; transform: none; }
    .project-tab .num { color: #ff2442; font-size: 15px; font-weight: 1000; line-height: 1; }
    .project-tab strong { display: block; margin-top: 10px; font-size: 18px; line-height: 1.25; }
    .project-feature { order: -1; overflow: hidden; border: 1px solid var(--brand-line-light); border-radius: var(--radius-media); background: var(--brand-paper-raised); box-shadow: 0 24px 60px rgba(17,17,17,.12); }
    .project-feature-top { position: relative; min-height: 320px; background: #101010; color: #fff; padding: 28px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; }
    .project-feature-top::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(16,16,16,.94) 0%, rgba(16,16,16,.7) 38%, rgba(16,16,16,.12) 100%); z-index: 1; pointer-events: none; }
    .project-feature-top img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: saturate(.95) contrast(1.04); }
    .project-feature-top > *:not(img) { position: relative; z-index: 2; }
    .project-feature-top .num { color: #ff2442; font-size: 48px; font-weight: 1000; line-height: 1; }
    .project-feature-kicker { max-width: 520px; margin: 0; color: rgba(255,255,255,.72); font-weight: 800; }
    .project-feature-body { padding: 28px; }
    .project-feature h3 { margin: 18px 0 0; font-size: clamp(38px, 5vw, 72px); line-height: .95; letter-spacing: 0; }
    .project-feature p { color: rgba(17,17,17,.62); line-height: 1.9; }
    .project-hint { display: inline-flex; margin-top: 18px; color: rgba(17,17,17,.42); font-size: 13px; font-weight: 800; }
    a:focus-visible, button:focus-visible { outline: 3px solid #ff2442; outline-offset: 4px; }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
    .card { min-height: 250px; padding: 24px; border: 1px solid rgba(255, 255, 255, .1); border-radius: 8px; background: rgba(255, 255, 255, .05); }
    .card strong { display: block; margin-bottom: 12px; font-size: 22px; line-height: 1.15; }
    .card p { margin: 0; color: rgba(255, 255, 255, .66); }
    .tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
    .tag { padding: 6px 9px; border-radius: 999px; background: rgba(255, 255, 255, .1); color: rgba(255,255,255,.82); font-size: 12px; font-weight: 800; }
    #method { background: #f4f1ea; color: #111; }
    .projects .section-note, #method .section-note, .projects .card p, #method .card p { color: #56534d; }
    .projects .card, #method .card { background: rgba(255, 255, 255, .68); border-color: rgba(17, 17, 17, .1); }
    .projects .tag { background: #e4ddd1; color: #3f3328; }
    .contact { display: grid; grid-template-columns: minmax(0, .86fr) minmax(280px, 1fr); gap: 28px; align-items: stretch; }
    .contact-panel { padding: 28px; border: 1px solid rgba(255, 255, 255, .1); border-radius: 8px; background: rgba(255, 255, 255, .05); }
    .contact-panel a, .contact-panel span { display: block; font-size: clamp(20px, 3vw, 34px); font-weight: 900; line-height: 1.25; word-break: break-word; }
    .disclaimer { margin-top: 18px; color: rgba(255,255,255,.56); font-size: 14px; }
    footer { padding: 28px clamp(20px, 6vw, 88px) 44px; color: rgba(255,255,255,.42); background: #0c0c0c; font-size: 13px; }
    @media (max-width: 900px) {
      .nav { align-items: flex-start; flex-direction: column; }
      .nav-links { width: 100%; overflow-x: auto; padding-bottom: 2px; }
      .hero { grid-template-columns: 1fr; min-height: auto; }
      .visual { min-height: 540px; border-left: 0; border-top: 1px solid rgba(255, 255, 255, .08); padding: 22px 0 0; }
      .signal { position: static; width: 100%; margin-bottom: 10px; }
      .signal { display: none; }
      .metrics { left: 0; bottom: 8px; }
      .section-head, .contact { display: block; }
      .section-note, .contact-panel + .contact-panel { margin-top: 16px; }
      .grid, .about-cards, .timeline-layout, .cap-head, .cap-grid, .project-layout, .result-grid { grid-template-columns: 1fr; }
      .result-card { border-right: 0; border-bottom: 1px solid rgba(255,255,255,.1); }
      .result-card:last-child { border-bottom: 0; }
      .timeline-detail { min-height: auto; }
      .card { min-height: auto; }
    }
    @media (max-width: 1180px) {
      .signal { display: none; }
      .cap-card { grid-template-columns: 88px minmax(0, 1fr); gap: 12px 24px; }
      .cap-index { grid-column: 1; grid-row: 1 / span 3; }
      .cap-card strong, .cap-card p, .cap-card .tag-row { grid-column: 2; }
      .cap-card .tag-row { justify-content: flex-start; max-width: none; }
    }
    @media (max-width: 640px) {
      body { background: #f6f6f4; }
      .page { width: calc(100% - 18px); margin: 8px auto 18px; border-radius: 24px; background: #0c0c0c; }
      .nav { flex-direction: row; align-items: center; }
      .nav { position: absolute; left: 0; right: 0; top: 0; padding: 26px 24px 10px; border-bottom: 0; background: transparent; }
      .brand { display: grid; gap: 1px; color: #fff; font-size: 21px; line-height: 1; letter-spacing: .14em; text-transform: uppercase; }
      .brand span:last-child { font-size: 13px; letter-spacing: .32em; }
      .nav-links { display: none; }
      .mobile-menu { display: inline-flex; align-items: center; justify-content: center; min-width: 94px; height: 44px; padding: 0 14px; border: 1px solid rgba(255,255,255,.28); border-radius: var(--radius-control); background: rgba(0,0,0,.18); color: #fff; font-size: 13px; font-weight: 800; }
      .hero { display: block; min-height: clamp(700px, 188vw, 740px); padding: 116px 24px 30px; border-radius: 24px 24px 0 0; overflow: hidden; }
      .hero > div:first-child { position: relative; z-index: 4; max-width: min(270px, 72vw); }
      .eyebrow { margin-bottom: 20px; border: 0; background: transparent; padding: 0; color: #ff2442; font-size: 12px; letter-spacing: .05em; }
      .hero-name { font-size: clamp(58px, 17vw, 74px); line-height: .88; }
      .hero-chinese { margin-top: 6px; font-size: 44px; line-height: 1; }
      .hero-copy { margin-top: 22px; color: rgba(255,255,255,.78); font-size: 16px; line-height: 1.85; }
      .hero-actions { display: flex; align-items: center; flex-wrap: wrap; width: min(260px, 72vw); gap: 10px 16px; margin-top: 24px; }
      .secondary-actions { display: none; }
      .hero-meta, .focus-row { display: none; }
      .button { min-height: 48px; justify-content: center; }
      .hero-text-link { min-height: 36px; }
      .button.secondary { background: rgba(12,12,12,.42); border-color: rgba(255,255,255,.42); }
      .visual { position: absolute; inset: 106px -84px auto 108px; height: 680px; min-height: 0; border-top: 0; padding: 0; }
      .visual::before { inset: 8% 0 0; }
      .visual img { width: min(100%, 430px); max-height: 620px; transform: translateY(74px); }
      .metrics { display: none; }
      .metric small { font-size: 9px; letter-spacing: .12em; }
      .metric strong { font-size: 14px; }
      .about-section { margin-top: -1px; border-radius: 24px 24px 0 0; padding: 44px 24px 48px; }
      .about-title { max-width: 300px; font-size: 42px; line-height: 1.04; }
      .about-cards { margin-top: 28px; }
      .about-card { min-height: auto; border-radius: 18px; padding: 22px; }
      .about-card strong { margin-top: 18px; font-size: 23px; }
      .about-card p { margin-top: 12px; line-height: 1.75; }
      section { padding: 46px 24px; }
      h2 { font-size: 34px; line-height: 1.06; }
      .section-head { margin-bottom: 22px; }
      .timeline-layout, .project-layout { margin-top: 26px; }
      .timeline-card, .cap-card { display: grid; grid-template-columns: 1fr; gap: 10px; padding: 20px 0; }
      .cap-card .tag-row { justify-content: flex-start; max-width: none; }
      .cap-grid { margin-top: 24px; }
      .project-list { grid-template-columns: 1fr; }
      .project-tab, .project-tab + .project-tab { padding: 16px 0; border-left: 0; }
      .project-feature { border-radius: 20px; }
      .project-feature-top { min-height: 230px; padding: 22px; }
      .project-feature-body { padding: 22px; }
      .project-feature h3 { font-size: 34px; line-height: 1.05; }
      .contact { padding-top: 48px; padding-bottom: 56px; }
      .contact-panel { border-radius: 20px; padding: 20px; }
      .contact-panel a { font-size: 18px; }
    }
    @media (max-width: 390px) {
      .page { width: calc(100% - 12px); margin-top: 6px; border-radius: 22px; }
      .nav { padding-left: 20px; padding-right: 20px; }
      .hero { padding-left: 20px; padding-right: 20px; }
      .hero > div:first-child { max-width: 246px; }
      .hero-name { font-size: clamp(54px, 16vw, 66px); }
      .hero-chinese { font-size: 39px; }
      .hero-copy { font-size: 15px; line-height: 1.78; }
      .visual { inset: 132px -118px auto 86px; }
      .metrics { left: -72px; right: 112px; bottom: 104px; }
      section { padding-left: 20px; padding-right: 20px; }
    }
  </style>
</head>
<body>
  <main class="page">
    <nav class="nav" aria-label="公开资料导航">
      <a class="brand" href="/profile"><span>Nelson</span><span>Archive</span></a>
      <div class="nav-links">
        <a href="#results">关键结果</a>
        <a href="#capabilities">能力</a>
        <a href="#projects">项目</a>
        <a href="#timeline">经历</a>
        <a href="#contact">联系</a>
        <a class="login-link" href="/me/login">私密案例登录</a>
      </div>
      <a class="mobile-menu" href="/me/login" aria-label="进入私密案例登录">案例登录</a>
    </nav>
    <header class="hero">
      <div>
        <p class="eyebrow">AI + C 端消费者产品负责人</p>
        <h1 class="hero-name">Nelson</h1>
        <h2 class="hero-chinese">何坚松</h2>
        <p class="hero-copy">把 AI 能力、消费者需求与商品经营，做成可落地的产品增长。9 年大健康、快消、新消费与品牌出海经验，主导或深度参与孵化产品累计销售规模 11.2 亿+。</p>
        <div class="hero-actions">
          <a class="button" href="#projects">查看代表项目</a>
          <a class="hero-text-link" href="#timeline">职业轨迹</a>
          <a class="hero-text-link" href="#contact">联系</a>
        </div>
        <div class="hero-meta">
          <span>北京</span>
          <span>9 年产品与品牌经验</span>
          <span>AI 消费者产品负责人</span>
        </div>
        <div class="focus-row">
          <span>AI 消费者产品</span>
          <span>产品企划</span>
          <span>商品经营</span>
          <span>GTM</span>
        </div>
      </div>
      <aside class="visual" aria-label="个人能力视觉展示">
        <div class="signal">
          <span>AI PRODUCT</span>
          <span>CONSUMER</span>
          <span>GTM</span>
        </div>
        <img src="/profile-assets/nelson-hero-character.webp" alt="何坚松个人网站视觉形象" fetchpriority="high" decoding="async" />
        <div class="metrics" aria-label="经历路径">
          <div class="metric"><small>产品</small><strong>AI</strong></div>
          <div class="metric"><small>场景</small><strong>C端</strong></div>
          <div class="metric"><small>经营</small><strong>GTM</strong></div>
        </div>
      </aside>
    </header>
    <section class="results-section" id="results" aria-labelledby="results-title">
      <div class="section-inner">
        <div class="section-head">
          <div>
            <p class="eyebrow">Selected Results</p>
            <h2 id="results-title">关键结果</h2>
          </div>
          <p class="section-note">用业务规模、品牌增长和 AI 工具落地，呈现从产品定义到持续经营的完整能力。</p>
        </div>
        <div class="result-grid">
          <article class="result-card"><small>01 / SCALE</small><div><strong>11.2亿+</strong><p>主导或深度参与孵化产品累计销售规模</p></div></article>
          <article class="result-card"><small>02 / BRAND</small><div><strong>1.4亿元</strong><p>益口葛葛 3.5 年累计销售额</p></div></article>
          <article class="result-card"><small>03 / MARKET</small><div><strong>10亿港元</strong><p>泰安品牌年度销售规模</p></div></article>
          <article class="result-card"><small>04 / AI BUILD</small><div><strong>10+</strong><p>AI Agent、自动化工作流与数据工具完成可运行原型或实际部署</p></div></article>
        </div>
      </div>
    </section>
    <section class="about-section" id="about" aria-labelledby="about-title">
      <div class="section-inner">
        <p class="eyebrow">About Nelson</p>
        <h2 class="about-title" id="about-title">让 AI 产品真正进入消费者场景与经营结果。</h2>
        <div class="about-cards">
          <article class="about-card"><small>用户</small><strong>真实需求，而不是技术想象。</strong><p>从问卷、评论、市场变化与竞品信号中识别问题，形成场景排序、产品假设和验证清单。</p></article>
          <article class="about-card"><small>产品</small><strong>从概念走向可验证方案。</strong><p>将大模型、Agent、知识库、智能硬件与内容能力转译为产品功能、交互体验和阶段路线图。</p></article>
          <article class="about-card"><small>经营</small><strong>从上市走向持续增长。</strong><p>连接 SKU、价格带、渠道货盘、内容表达、销售结构、库存健康与 ROI 复盘。</p></article>
        </div>
      </div>
    </section>
    <section class="timeline-section" id="timeline" aria-labelledby="timeline-title">
      <div class="section-inner">
        <div class="section-head">
          <div>
            <p class="eyebrow">Timeline</p>
            <h2 id="timeline-title">经历时间线</h2>
          </div>
          <p class="section-note">仅保留公司、岗位和职责定位，完整项目明细在私人档案中查看。</p>
        </div>
        <div class="timeline-layout">
          <div class="timeline-list">
            <article class="timeline-card"><small>01 / 2025—NOW</small><strong>消费品品牌<br>北京</strong><p>产品企划总监，负责 AI 消费者产品、商品管理与 GTM 协同，把用户场景、产品结构与经营结果放在同一条链路推进。</p></article>
            <article class="timeline-card"><small>02 / 2022—2025</small><strong>深圳市味康嘉品健康科技<br>深圳</strong><p>产品总监，负责消费品牌孵化、产品创新、渠道增长与团队管理，建立从新品定义到上市复盘的协同机制。</p></article>
            <article class="timeline-card"><small>03 / 2017—2022</small><strong>香港科朗集团—中科食品<br>香港</strong><p>品牌经理，负责品牌出海、本地化、渠道运营与消费者运营，连接产品表达与区域市场承接。</p></article>
          </div>
        </div>
      </div>
    </section>
    <section class="cap-section" id="capabilities" aria-labelledby="capabilities-title">
      <div class="section-inner">
        <div class="cap-head">
          <div>
            <p class="eyebrow">Capability Map</p>
            <h2 id="capabilities-title">能力板块</h2>
          </div>
          <p class="section-note">从机会识别、产品定义到上市经营，让每一次产品判断都有证据、有路径、有结果。</p>
        </div>
        <div class="cap-grid">
          <article class="cap-card"><span class="cap-index">01</span><strong>AI 消费者产品规划</strong><p>围绕真实用户场景，将大模型、Agent、知识库、智能硬件与内容能力转化为明确的产品功能、交互体验、验证指标和阶段路线图。</p><div class="tag-row"><span class="tag">AI应用</span><span class="tag">Agent工作流</span><span class="tag">智能硬件</span><span class="tag">产品路线图</span></div></article>
          <article class="cap-card"><span class="cap-index">02</span><strong>消费者洞察与产品定义</strong><p>将问卷、用户评论、市场趋势与竞品信息转化为痛点分类、场景排序、需求优先级和验证清单，让产品决策建立在连续证据上。</p><div class="tag-row"><span class="tag">消费者洞察</span><span class="tag">需求管理</span><span class="tag">产品定义</span><span class="tag">用户验证</span></div></article>
          <article class="cap-card"><span class="cap-index">03</span><strong>商品企划与 GTM</strong><p>从品类机会、产品分级、SKU 组合、价格带和渠道货盘出发，连接产品开发、品牌表达、内容验证、渠道承接与销售复盘。</p><div class="tag-row"><span class="tag">商品企划</span><span class="tag">SKU管理</span><span class="tag">渠道货盘</span><span class="tag">GTM</span></div></article>
          <article class="cap-card"><span class="cap-index">04</span><strong>经营分析与组织协同</strong><p>围绕销售结构、库存健康、利润和 ROI 复盘经营表现，并推动研发、供应链、品牌、渠道、合规和算法团队围绕同一目标协作。</p><div class="tag-row"><span class="tag">经营分析</span><span class="tag">ROI拆解</span><span class="tag">跨部门协同</span><span class="tag">团队管理</span></div></article>
        </div>
      </div>
    </section>
    <section class="projects" id="projects" aria-labelledby="projects-title">
      <div class="section-inner">
        <div class="section-head">
          <div>
            <p class="eyebrow">Project Archive</p>
            <h2 id="projects-title">项目作品</h2>
          </div>
          <p class="section-note">开放页只呈现方向、关键动作与业务结果；完整过程和证明材料进入私人档案。</p>
        </div>
        <div class="project-layout">
          <div class="project-list" role="tablist" aria-label="公开项目切换">
            <button class="project-tab is-active" type="button" role="tab" aria-selected="true" data-project="jikex001"><span class="num">01</span><strong>AI 消费者产品线 0—1 搭建</strong><div class="tag-row"><span class="tag">AI应用</span><span class="tag">智能硬件</span><span class="tag">产品路线图</span></div></button>
            <button class="project-tab" type="button" role="tab" aria-selected="false" data-project="agentstack"><span class="num">02</span><strong>AI Agent 与产品决策工具体系</strong><div class="tag-row"><span class="tag">Agent工作流</span><span class="tag">数据工具</span><span class="tag">业务落地</span></div></button>
            <button class="project-tab" type="button" role="tab" aria-selected="false" data-project="yikougege"><span class="num">03</span><strong>益口葛葛功能性提神食品</strong><div class="tag-row"><span class="tag">新品类定义</span><span class="tag">消费品牌</span><span class="tag">GTM增长</span></div></button>
          </div>
          <article class="project-feature" aria-live="polite">
            <div class="project-feature-top">
              <img id="project-image" src="/profile-assets/projects/jikex001/assets/product-house.webp" alt="AI 消费者产品线 0—1 搭建项目图" loading="lazy" decoding="async" />
              <span class="num" id="project-index">01</span>
              <p class="project-feature-kicker" id="project-kicker">AI CONSUMER PRODUCT / 从短期试点到长期软硬件闭环。</p>
            </div>
            <div class="project-feature-body">
              <div class="pill-row" id="project-tags"><span class="tag">AI应用</span><span class="tag">智能硬件</span><span class="tag">产品路线图</span></div>
              <h3 id="project-title">AI 消费者产品线 0—1 搭建</h3>
              <p id="project-copy">面向陪伴与亲密关系消费场景，从 0 规划 AI 消费者产品方向，建立“短期 AI 应用试点—中期数据能力沉淀—长期软硬件闭环”的阶段路线图。</p>
              <span class="project-hint">公开页仅支持切换浏览，不开放项目详情入口。</span>
            </div>
          </article>
        </div>
      </div>
    </section>
    <section id="method" aria-labelledby="method-title">
      <div class="section-head">
        <h2 id="method-title">从真实需求出发，让每一次产品判断都有证据、有路径、有结果。</h2>
        <p class="section-note">识别机会、定义产品、推动落地、持续经营，把模糊机会推进成团队能执行、市场能验证、业务能复盘的产品系统。</p>
      </div>
    </section>
    <section class="contact" id="contact" aria-labelledby="contact-title">
      <div>
        <p class="eyebrow">Contact</p>
        <h2 id="contact-title">联系何坚松</h2>
        <p class="disclaimer">适合交流：C 端 AI 应用、AI 陪伴产品、智能硬件、消费者洞察、商品企划、产品经营与 GTM。完整案例和证明材料在私密站内查看。</p>
      </div>
      <div class="contact-panel">
        <a href="mailto:kinsongho@qq.com">kinsongho@qq.com</a>
        <a href="mailto:sososong28@gmail.com">sososong28@gmail.com</a>
        <span>北京</span>
      </div>
    </section>
  </main>
  <footer>© 2026 何坚松。公开页内容已做脱敏处理。</footer>
  <script>
    const publicProjects = {
      jikex001: {
        index: "01",
        image: "/profile-assets/projects/jikex001/assets/product-house.webp",
        alt: "AI 消费者产品线 0—1 搭建项目图",
        kicker: "AI CONSUMER PRODUCT / 从短期试点到长期软硬件闭环。",
        tags: ["AI应用", "智能硬件", "产品路线图"],
        title: "AI 消费者产品线 0—1 搭建",
        copy: "面向陪伴与亲密关系消费场景，从 0 规划 AI 消费者产品方向，建立“短期 AI 应用试点—中期数据能力沉淀—长期软硬件闭环”的阶段路线图。"
      },
      agentstack: {
        index: "02",
        image: "/profile-assets/projects/jikex001/assets/consumer-survey-painpoints.png",
        alt: "AI Agent 与产品决策工具体系数据图",
        kicker: "AI WORKFLOW / 从一次性分析到持续更新的业务工作流。",
        tags: ["Agent工作流", "数据工具", "业务落地"],
        title: "AI Agent 与产品决策工具体系",
        copy: "围绕产品决策、消费者洞察、竞品监控、知识检索、经营复盘和内容生产，完成 10+ 个 AI Agent、自动化工作流与数据工具的可运行原型或部署；累计采集与处理 3 万+ 条原始市场与竞品信息。"
      },
      yikougege: {
        index: "03",
        image: "/profile-assets/projects/yikougege/assets/product-family.jpg",
        alt: "益口葛葛功能性提神食品产品组合图",
        kicker: "FUNCTIONAL FOOD / 从新品类定义到渠道与内容协同增长。",
        tags: ["新品类定义", "消费品牌", "GTM增长"],
        title: "益口葛葛功能性提神食品",
        copy: "从加班、熬夜、考试等高频场景切入，完成新品类定义、产品迭代、品牌资产、渠道铺设和复购机制建设；3.5 年累计销售 1.4 亿元，峰值月销 2,000 万。"
      }
    };

    const projectTabs = document.querySelectorAll(".project-tab[data-project]");
    const projectImage = document.getElementById("project-image");
    const projectIndex = document.getElementById("project-index");
    const projectKicker = document.getElementById("project-kicker");
    const projectTags = document.getElementById("project-tags");
    const projectTitle = document.getElementById("project-title");
    const projectCopy = document.getElementById("project-copy");

    projectTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const data = publicProjects[tab.dataset.project];
        if (!data) return;
        projectTabs.forEach((item) => {
          const active = item === tab;
          item.classList.toggle("is-active", active);
          item.setAttribute("aria-selected", active ? "true" : "false");
        });
        projectImage.src = data.image;
        projectImage.alt = data.alt;
        projectIndex.textContent = data.index;
        projectKicker.textContent = data.kicker;
        projectTags.innerHTML = data.tags.map((tag) => `<span class="tag">${tag}</span>`).join("");
        projectTitle.textContent = data.title;
        projectCopy.textContent = data.copy;
      });
    });
  </script>
</body>
</html>
"""


LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>私密个人档案登录</title>
  <style>
    * { box-sizing: border-box; }
    :root { color-scheme: light; --ink: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --bg: #f5f5f7; --panel: #ffffff; --blue: #0071e3; --teal: #00a3a3; --amber: #b76e00; }
    html { scroll-behavior: smooth; }
    body { margin: 0; min-height: 100vh; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: var(--ink); background: var(--bg); }
    a { color: var(--blue); text-decoration: none; }
    .login-shell { min-height: 100vh; display: grid; grid-template-columns: minmax(0, 1.18fr) minmax(360px, .82fr); align-items: stretch; }
    .visual { position: relative; display: grid; align-content: center; min-height: 620px; padding: 70px 6vw; overflow: hidden; background: #fbfbfd; isolation: isolate; }
    .visual::before { content: ""; position: absolute; width: 70vw; height: 70vw; left: 12%; top: -26%; z-index: -1; border-radius: 999px; background: radial-gradient(circle, rgba(0, 113, 227, .16), rgba(0, 163, 163, .08) 36%, transparent 68%); filter: blur(28px); animation: ambientShift 12s ease-in-out infinite alternate; }
    .visual::after { content: ""; position: absolute; inset: 0; z-index: -1; background: linear-gradient(115deg, transparent 0 38%, rgba(255, 255, 255, .68) 48%, transparent 60%); transform: translateX(-80%); animation: glassSweep 5.8s ease-in-out infinite; }
    .visual img { width: min(100%, 980px); height: auto; display: block; margin: 0 auto; filter: drop-shadow(0 34px 70px rgba(29, 29, 31, .14)); transform: translateY(8px); animation: rise .8s ease-out both, imageFloat 7s ease-in-out .9s infinite; will-change: transform; }
    .visual-copy { max-width: 760px; margin: 0 auto 22px; }
    .visual-copy > * { animation: copyIn .72s cubic-bezier(.2, .8, .2, 1) both; }
    .visual-copy h1 { animation-delay: .08s; }
    .visual-copy p:last-child { animation-delay: .18s; }
    .eyebrow { margin: 0 0 12px; color: var(--blue); font-size: 13px; font-weight: 800; letter-spacing: 0; }
    .visual h1 { margin: 0; font-size: 58px; line-height: 1.05; font-weight: 850; }
    .visual p { max-width: 620px; margin: 18px 0 0; color: var(--muted); font-size: 19px; line-height: 1.55; }
    .login-panel { display: grid; place-items: center; padding: 48px; background: rgba(255, 255, 255, .78); border-left: 1px solid rgba(210, 210, 215, .75); backdrop-filter: blur(24px); }
    .box { width: min(100%, 410px); animation: panelIn .78s cubic-bezier(.2, .8, .2, 1) .12s both; }
    .box h2 { margin: 0 0 10px; font-size: 34px; line-height: 1.14; }
    .box > p { margin: 0 0 28px; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .field { margin-bottom: 16px; }
    label { display: block; margin-bottom: 8px; color: #424245; font-size: 13px; font-weight: 750; }
    input { width: 100%; height: 48px; border: 1px solid var(--line); border-radius: 8px; padding: 0 14px; color: var(--ink); background: rgba(255, 255, 255, .92); font-size: 15px; outline: none; transition: border-color .18s ease, box-shadow .18s ease, background .18s ease; }
    input:focus { border-color: var(--blue); background: #fff; box-shadow: 0 0 0 4px rgba(0, 113, 227, .12); }
    button { position: relative; overflow: hidden; width: 100%; height: 48px; border: none; border-radius: 8px; color: #fff; background: var(--blue); font-size: 15px; font-weight: 800; cursor: pointer; transition: transform .18s ease, background .18s ease, box-shadow .18s ease; box-shadow: 0 12px 26px rgba(0, 113, 227, .24); }
    button::before { content: ""; position: absolute; inset: 0; background: linear-gradient(105deg, transparent 0 34%, rgba(255, 255, 255, .38) 48%, transparent 62%); transform: translateX(-120%); transition: transform .7s ease; }
    button:hover::before { transform: translateX(120%); }
    button:hover { background: #0077ed; transform: translateY(-1px); }
    .error { margin-bottom: 16px; padding: 12px 14px; border: 1px solid #ffd0d2; border-radius: 8px; color: #b42318; background: #fff1f2; font-size: 13px; font-weight: 800; }
    .footer { margin-top: 18px; color: #86868b; font-size: 12px; text-align: center; }
    @keyframes rise { from { opacity: 0; transform: translateY(26px) scale(.985); } to { opacity: 1; transform: translateY(8px) scale(1); } }
    @keyframes imageFloat { 0%, 100% { transform: translateY(8px); } 50% { transform: translateY(-5px); } }
    @keyframes copyIn { from { opacity: 0; transform: translateY(22px); filter: blur(8px); } to { opacity: 1; transform: translateY(0); filter: blur(0); } }
    @keyframes panelIn { from { opacity: 0; transform: translateY(26px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes ambientShift { from { transform: translate3d(-3%, 2%, 0) scale(.95); } to { transform: translate3d(8%, 7%, 0) scale(1.08); } }
    @keyframes glassSweep { 0%, 38% { transform: translateX(-80%); opacity: 0; } 52% { opacity: 1; } 74%, 100% { transform: translateX(82%); opacity: 0; } }
    @media (prefers-reduced-motion: reduce) { .visual::before, .visual::after, .visual img, .visual-copy > *, .box, button { animation: none; transition: none; } }
    @media (max-width: 920px) {
      .login-shell { grid-template-columns: 1fr; }
      .visual { min-height: auto; padding: 48px 20px 20px; }
      .visual h1 { font-size: 40px; }
      .visual p { font-size: 16px; }
      .login-panel { padding: 26px 20px 46px; border-left: none; }
    }
  </style>
</head>
<body>
  <main class="login-shell">
    <section class="visual" aria-label="私密档案视觉">
      <div class="visual-copy">
        <p class="eyebrow">Private Profile</p>
        <h1>你的经历，像产品一样被认真呈现。</h1>
        <p>当前站点保持私密访问。登录后进入个人介绍、经历时间线、项目作品与私密资料中心。</p>
      </div>
      <img src="{{ url_for('static', filename='profile-archive-hero.png') }}" alt="私密档案库视觉图" />
    </section>
    <section class="login-panel">
      <div class="box">
        <h2>私密个人档案</h2>
        <p>使用授权账号进入 `/me`，所有资料只在登录后查看。</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
          <input type="hidden" name="next" value="{{ next_path }}" />
          <div class="field"><label for="username">账号</label><input id="username" name="username" value="{{ username }}" autocomplete="username" autofocus /></div>
          <div class="field"><label for="password">密码</label><input id="password" name="password" type="password" autocomplete="current-password" /></div>
          <button type="submit">登录</button>
        </form>
        <div class="footer">/me · private access</div>
      </div>
    </section>
  </main>
</body>
</html>
"""


HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>私密个人档案</title>
  <style>
    * { box-sizing: border-box; }
    :root { color-scheme: light; --ink: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --bg: #f5f5f7; --panel: #ffffff; --blue: #0071e3; --teal: #008f8c; --amber: #b76e00; --dark: #111113; --scroll: 0; --pointer-x: 50vw; --pointer-y: 35vh; --hero-x: 0px; --hero-y: 0px; --hero-rx: 0deg; --hero-ry: 0deg; }
    html { scroll-behavior: smooth; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: var(--ink); background: var(--bg); }
    a { color: inherit; text-decoration: none; }
    .scroll-progress { position: fixed; top: 0; left: 0; z-index: 60; width: 100%; height: 3px; background: linear-gradient(90deg, #0071e3, #00a3a3, #f5a623); transform: scaleX(var(--scroll)); transform-origin: left center; box-shadow: 0 0 22px rgba(0, 113, 227, .32); pointer-events: none; }
    .ambient-light { position: fixed; left: 0; top: 0; z-index: 0; width: 420px; height: 420px; border-radius: 999px; pointer-events: none; transform: translate3d(calc(var(--pointer-x) - 210px), calc(var(--pointer-y) - 210px), 0); background: radial-gradient(circle, rgba(0, 113, 227, .12), rgba(0, 163, 163, .07) 38%, transparent 68%); filter: blur(18px); opacity: .78; transition: transform .25s ease-out, opacity .25s ease-out; }
    .nav { position: sticky; top: 0; z-index: 20; border-bottom: 1px solid rgba(210, 210, 215, .72); background: rgba(251, 251, 253, .82); backdrop-filter: saturate(180%) blur(22px); transition: background .22s ease, box-shadow .22s ease; }
    .nav.is-scrolled { background: rgba(251, 251, 253, .92); box-shadow: 0 16px 36px rgba(29, 29, 31, .08); }
    .nav-inner { max-width: 1180px; min-height: 54px; margin: 0 auto; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
    .brand { font-size: 15px; font-weight: 850; }
    .nav-links { display: flex; align-items: center; gap: 24px; color: #424245; font-size: 13px; }
    .nav-links a { transition: color .18s ease; }
    .nav-links a:hover { color: var(--blue); }
    .nav-status { display: flex; align-items: center; gap: 10px; color: #424245; font-size: 13px; }
    .mode { color: var(--blue); font-weight: 800; }
    .logout { padding: 7px 12px; border: 1px solid rgba(0, 113, 227, .25); border-radius: 8px; color: var(--blue); background: rgba(255, 255, 255, .72); font-weight: 800; }
    main { position: relative; z-index: 1; overflow: hidden; }
    .section-inner { max-width: 1180px; margin: 0 auto; padding: 0 28px; }
    .hero { position: relative; padding: 58px 0 42px; background: #fbfbfd; overflow: hidden; }
    .hero::before { content: ""; position: absolute; inset: -20% -10% auto auto; width: 58vw; height: 58vw; border-radius: 999px; background: radial-gradient(circle, rgba(0, 113, 227, .14), rgba(0, 143, 140, .08) 36%, transparent 68%); filter: blur(26px); animation: slowOrbit 16s ease-in-out infinite alternate; }
    .hero-grid { display: grid; grid-template-columns: minmax(0, .98fr) minmax(480px, 1.02fr); gap: 34px; align-items: center; }
    .eyebrow { margin: 0 0 14px; color: var(--blue); font-size: 14px; font-weight: 850; letter-spacing: 0; }
    h1 { max-width: 690px; margin: 0; font-size: 64px; line-height: 1.02; font-weight: 880; }
    .lead { max-width: 640px; margin: 24px 0 0; color: var(--muted); font-size: 20px; line-height: 1.55; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
    .action { display: inline-flex; align-items: center; min-height: 40px; padding: 0 16px; border-radius: 8px; font-size: 15px; font-weight: 800; }
    .primary { color: #fff; background: var(--blue); }
    .secondary { color: var(--blue); background: rgba(0, 113, 227, .08); }
    .hero-copy > * { animation: textLift .75s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-copy h1 { animation-delay: .08s; }
    .hero-copy .lead { animation-delay: .16s; }
    .hero-copy .hero-actions { animation-delay: .24s; }
    .hero-media { position: relative; perspective: 1200px; animation: heroIn .82s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-media::before { content: ""; position: absolute; inset: 10% 4% 0; border-radius: 18px; background: radial-gradient(circle at 50% 40%, rgba(0, 113, 227, .18), transparent 58%); filter: blur(30px); transform: translateY(8px); }
    .hero-media::after { content: ""; position: absolute; inset: 0; border-radius: 8px; background: linear-gradient(108deg, transparent 0 38%, rgba(255, 255, 255, .72) 48%, transparent 60%); transform: translateX(-90%); animation: heroSweep 6.4s ease-in-out infinite; pointer-events: none; }
    .hero-media img { position: relative; width: 100%; height: auto; display: block; border-radius: 8px; filter: drop-shadow(0 34px 70px rgba(29, 29, 31, .16)); transform: translate3d(var(--hero-x), var(--hero-y), 0) rotateX(var(--hero-rx)) rotateY(var(--hero-ry)); transition: transform .18s ease-out, filter .22s ease; will-change: transform; animation: mediaFloat 7.4s ease-in-out 1s infinite; }
    .status-bar { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin-top: 30px; border: 1px solid rgba(210, 210, 215, .85); border-radius: 8px; overflow: hidden; background: rgba(210, 210, 215, .85); }
    .status-item { padding: 18px 20px; background: rgba(255, 255, 255, .78); transition: background .22s ease, transform .22s ease; }
    .status-item:hover { background: rgba(255, 255, 255, .95); transform: translateY(-2px); }
    .status-label { color: var(--muted); font-size: 12px; font-weight: 750; }
    .status-value { margin-top: 5px; font-size: 18px; font-weight: 850; }
    .band { padding: 78px 0; }
    .band.dark { color: #f5f5f7; background: var(--dark); }
    .band.dark p, .band.dark .section-copy, .band.dark .small { color: #a1a1a6; }
    .section-title { max-width: 760px; margin: 0; font-size: 46px; line-height: 1.08; font-weight: 860; }
    .section-copy { max-width: 660px; margin: 16px 0 0; color: var(--muted); font-size: 18px; line-height: 1.65; }
    .feature-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 34px; }
    .feature-card { position: relative; overflow: hidden; isolation: isolate; min-height: 210px; padding: 24px; border: 1px solid rgba(210, 210, 215, .82); border-radius: 8px; background: var(--panel); box-shadow: 0 20px 55px rgba(29, 29, 31, .06); transition: transform .3s ease, box-shadow .3s ease, border-color .3s ease; }
    .feature-card::after, .project-card::after, .resource::after { content: ""; position: absolute; inset: 0; z-index: -1; opacity: 0; pointer-events: none; background: radial-gradient(520px circle at var(--glow-x, 50%) var(--glow-y, 30%), rgba(255, 255, 255, .88), transparent 42%); transition: opacity .28s ease; }
    .feature-card h3 { margin: 0 0 12px; font-size: 24px; line-height: 1.18; }
    .feature-card p { margin: 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .feature-kicker { margin-bottom: 18px; color: var(--teal); font-size: 13px; font-weight: 850; }
    .timeline { position: relative; display: grid; gap: 14px; margin-top: 34px; }
    .timeline::before { content: ""; position: absolute; left: 72px; top: 20px; bottom: 20px; width: 1px; background: linear-gradient(#66d9d5, rgba(102, 217, 213, .18)); transform: scaleY(var(--timeline-progress, 0)); transform-origin: top; transition: transform .8s cubic-bezier(.2, .8, .2, 1); }
    .timeline-item { position: relative; display: grid; grid-template-columns: 160px minmax(0, 1fr); gap: 24px; padding: 26px 0; border-top: 1px solid rgba(245, 245, 247, .2); }
    .timeline-item::before { content: ""; position: absolute; left: 66px; top: 31px; width: 13px; height: 13px; border-radius: 50%; background: #66d9d5; box-shadow: 0 0 0 0 rgba(102, 217, 213, .5); transform: scale(.65); transition: transform .35s ease, box-shadow .35s ease; }
    .timeline-item.is-visible::before { transform: scale(1); box-shadow: 0 0 0 8px rgba(102, 217, 213, .12); }
    .timeline-item:last-child { border-bottom: 1px solid rgba(245, 245, 247, .2); }
    .time { color: #66d9d5; font-size: 14px; font-weight: 850; }
    .label { display: inline-block; margin-top: 10px; color: #d2d2d7; font-size: 12px; font-weight: 800; }
    .timeline h3 { margin: 0 0 8px; color: #fff; font-size: 26px; line-height: 1.2; }
    .timeline p { margin: 0; max-width: 780px; font-size: 16px; line-height: 1.75; }
    .project-method { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 28px; align-items: start; margin-top: 30px; padding-top: 22px; border-top: 1px solid rgba(210, 210, 215, .82); }
    .method-label { color: var(--blue); font-size: 13px; font-weight: 850; }
    .method-copy { max-width: 760px; color: var(--muted); font-size: 16px; line-height: 1.72; }
    .project-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 34px; }
    .project-card { position: relative; overflow: hidden; isolation: isolate; display: flex; flex-direction: column; min-height: 318px; padding: 26px; border: 1px solid rgba(210, 210, 215, .82); border-radius: 8px; background: var(--panel); box-shadow: 0 20px 55px rgba(29, 29, 31, .055); transition: transform .3s ease, box-shadow .3s ease, border-color .3s ease; }
    .project-card h3 { margin: 0 0 12px; font-size: 30px; line-height: 1.12; }
    .project-card p { margin: 0; color: var(--muted); font-size: 16px; line-height: 1.7; }
    .project-card.large { display: grid; align-content: end; color: #f5f5f7; background: #19191d; }
    .project-card.large p { color: #a1a1a6; }
    .project-meta { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }
    .project-meta span { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border: 1px solid rgba(210, 210, 215, .86); border-radius: 999px; color: #424245; background: rgba(245, 245, 247, .74); font-size: 12px; font-weight: 820; }
    .proof-list { display: grid; gap: 10px; margin-top: 20px; padding-top: 18px; border-top: 1px solid rgba(210, 210, 215, .72); }
    .proof-line { display: grid; grid-template-columns: 76px minmax(0, 1fr); gap: 12px; color: var(--muted); font-size: 13px; line-height: 1.55; }
    .proof-line strong { color: #424245; font-size: 12px; font-weight: 850; }
    .project-card.large .project-meta span { color: #f5f5f7; border-color: rgba(245, 245, 247, .2); background: rgba(255, 255, 255, .08); }
    .project-card.large .proof-list { border-top-color: rgba(245, 245, 247, .16); }
    .project-card.large .proof-line { color: #a1a1a6; }
    .project-card.large .proof-line strong { color: #f5f5f7; }
    .case-link { display: inline-flex; align-items: center; width: fit-content; min-height: 38px; margin-top: auto; padding: 0 14px; border: 1px solid rgba(0, 113, 227, .24); border-radius: 8px; color: var(--blue); background: rgba(0, 113, 227, .08); font-size: 14px; font-weight: 850; transition: transform .22s ease, background .22s ease, border-color .22s ease; }
    .project-card > .small { margin-top: 0; }
    .small { margin-top: 18px; color: var(--muted); font-size: 13px; font-weight: 800; }
    .resource-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 34px; }
    .resource { position: relative; overflow: hidden; isolation: isolate; min-height: 188px; padding: 22px; border: 1px solid rgba(245, 245, 247, .16); border-radius: 8px; background: rgba(255, 255, 255, .08); transition: transform .3s ease, border-color .3s ease, background .3s ease; }
    .resource h3 { margin: 0 0 10px; font-size: 20px; line-height: 1.2; }
    .resource p { margin: 0; color: #a1a1a6; font-size: 14px; line-height: 1.65; }
    .footer-band { padding: 42px 0 54px; color: var(--muted); background: #fbfbfd; font-size: 13px; }
    .motion-ready .reveal { opacity: 0; transform: translateY(34px); filter: blur(10px); transition: opacity .8s cubic-bezier(.2, .8, .2, 1), transform .8s cubic-bezier(.2, .8, .2, 1), filter .8s ease; transition-delay: var(--delay, 0ms); }
    .motion-ready .reveal.is-visible { opacity: 1; transform: translateY(0); filter: blur(0); }
    @media (hover: hover) {
      .feature-card:hover, .project-card:hover { transform: translateY(-6px); border-color: rgba(0, 113, 227, .28); box-shadow: 0 28px 70px rgba(29, 29, 31, .12); }
      .resource:hover { transform: translateY(-5px); border-color: rgba(102, 217, 213, .34); background: rgba(255, 255, 255, .115); }
      .feature-card:hover::after, .project-card:hover::after, .resource:hover::after { opacity: .45; }
      .action:hover, .logout:hover, .case-link:hover { transform: translateY(-1px); }
    }
    @keyframes heroIn { from { opacity: 0; transform: translateY(28px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes textLift { from { opacity: 0; transform: translateY(26px); filter: blur(8px); } to { opacity: 1; transform: translateY(0); filter: blur(0); } }
    @keyframes mediaFloat { 0%, 100% { filter: drop-shadow(0 34px 70px rgba(29, 29, 31, .16)); } 50% { filter: drop-shadow(0 44px 86px rgba(29, 29, 31, .2)); } }
    @keyframes heroSweep { 0%, 34% { opacity: 0; transform: translateX(-90%); } 48% { opacity: .7; } 72%, 100% { opacity: 0; transform: translateX(92%); } }
    @keyframes slowOrbit { from { transform: translate3d(2%, -2%, 0) scale(.92); } to { transform: translate3d(-7%, 8%, 0) scale(1.08); } }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      .ambient-light, .scroll-progress { display: none; }
      .hero::before, .hero-media::after, .hero-media, .hero-media img, .hero-copy > *, .feature-card, .project-card, .resource, .status-item, .reveal { animation: none; transition: none; transform: none; filter: none; opacity: 1; }
    }
    @media (max-width: 980px) {
      .nav-inner { align-items: flex-start; flex-direction: column; padding: 13px 18px; }
      .nav-links { width: 100%; gap: 16px; overflow-x: auto; padding-bottom: 3px; }
      .nav-status { width: 100%; justify-content: space-between; }
      .section-inner { padding: 0 18px; }
      .hero { padding: 38px 0 30px; }
      .hero::before { inset: -72px 0 auto auto; width: 260px; height: 260px; }
      .hero-grid, .project-grid, .project-method { grid-template-columns: 1fr; }
      h1 { font-size: 42px; }
      .lead { font-size: 17px; }
      .section-title { font-size: 34px; }
      .feature-grid, .resource-grid, .status-bar { grid-template-columns: 1fr; }
      .band { padding: 56px 0; }
      .timeline::before, .timeline-item::before { display: none; }
      .timeline-item { grid-template-columns: 1fr; gap: 10px; }
      .timeline h3 { font-size: 22px; }
    }
  </style>
</head>
<body>
  <div class="scroll-progress" aria-hidden="true"></div>
  <div class="ambient-light" aria-hidden="true"></div>
  <header class="nav">
    <div class="nav-inner">
      <a class="brand" href="/me/">sososong / private profile</a>
      <nav class="nav-links" aria-label="页面导航">
        <a href="#intro">简介</a>
        <a href="#timeline">时间线</a>
        <a href="#projects">项目</a>
        <a href="#private">私密资料</a>
      </nav>
      <div class="nav-status"><span>当前登录：{{ username }}</span><span class="mode">私密模式</span><a class="logout" href="/me/logout">退出</a></div>
    </div>
  </header>
  <main>
    <section class="hero">
      <div class="section-inner">
        <div class="hero-grid">
          <div class="hero-copy">
            <p class="eyebrow">Private Profile Site</p>
            <h1>把经历、项目和资料，做成一个私密档案库。</h1>
            <p class="lead">当前站点只面向登录用户。它不是公开名片，而是一个可以长期沉淀个人介绍、关键经历、作品证据和私密材料的个人空间。</p>
            <div class="hero-actions">
              <a class="action primary" href="#projects">查看项目</a>
              <a class="action secondary" href="#private">进入资料区</a>
            </div>
          </div>
          <div class="hero-media">
            <img src="{{ url_for('static', filename='profile-archive-hero.png') }}" alt="私密档案库视觉图" />
          </div>
        </div>
        <div class="status-bar" aria-label="站点状态">
          <div class="status-item"><div class="status-label">访问范围</div><div class="status-value">仅登录用户可见</div></div>
          <div class="status-item"><div class="status-label">当前路径</div><div class="status-value">/me</div></div>
          <div class="status-item"><div class="status-label">内容状态</div><div class="status-value">私密整理中</div></div>
        </div>
      </div>
    </section>

    <section class="band" id="intro">
      <div class="section-inner">
        <h2 class="section-title">先让别人快速理解你，再展示证据。</h2>
        <p class="section-copy">这版首页按“个人产品页”的节奏组织内容：先给定位，再给经历，再给项目，最后进入私密资料。后续接入后台后，这些模块可以逐步变成可编辑内容。</p>
        <div class="feature-grid">
          <article class="feature-card"><div class="feature-kicker">Identity</div><h3>我是谁</h3><p>放个人介绍、当前身份、所在城市、擅长方向和希望别人如何理解你。</p></article>
          <article class="feature-card"><div class="feature-kicker">Focus</div><h3>当前方向</h3><p>围绕数据工具、自动化系统、个人知识库、内容生产和长期项目沉淀能力证据。</p></article>
          <article class="feature-card"><div class="feature-kicker">Boundary</div><h3>资料边界</h3><p>真实经历和未公开材料默认留在私密站；如果以后开放公开页，再挑选可公开内容。</p></article>
        </div>
      </div>
    </section>

    <section class="band dark" id="timeline">
      <div class="section-inner">
        <h2 class="section-title">经历时间线，保留阶段感。</h2>
        <p class="section-copy">适合记录工作、项目、学习、关键转折和阶段性成果。每一条都可以继续扩展成详情页。</p>
        <div class="timeline">
          <article class="timeline-item"><div><div class="time">现在</div><span class="label">私密站点</span></div><div><h3>个人经历网站上线到 /me</h3><p>当前先作为登录后档案页使用，后续可以继续扩展时间线、项目详情、资料下载和访客账号。</p></div></article>
          <article class="timeline-item"><div><div class="time">近期</div><span class="label">项目沉淀</span></div><div><h3>数据工具与自动化项目整理</h3><p>把已经做过的产品数据工具、自动化报告、知识库和内容系统整理成可回顾的项目记录。</p></div></article>
          <article class="timeline-item"><div><div class="time">待补充</div><span class="label">个人经历</span></div><div><h3>教育、工作、创业和重要节点</h3><p>后续按年份补充真实经历，每条记录保留日期、背景、做法、结果和相关资料。</p></div></article>
        </div>
      </div>
    </section>

    <section class="band" id="projects">
      <div class="section-inner">
        <h2 class="section-title">项目像一组卡片，先给判断，再给证据。</h2>
        <p class="section-copy">首页只保留一眼能懂的项目定位和证据入口；完整背景、素材、过程和结果放进详情页，避免把项目堆成一串普通列表。</p>
        <div class="project-method">
          <div class="method-label">Project index system</div>
          <div class="method-copy">这次借鉴社交卡片 skill 的做法：每张卡片只回答一个问题——这是什么项目、能证明什么、下一步看哪里。图片和长文不在首页堆叠，作为详情页里的证据层出现。</div>
        </div>
        <div class="project-grid">
          <article class="project-card">
            <div class="small">BRAND PROJECT 01</div>
            <h3>益口葛葛</h3>
            <div class="project-meta"><span>品牌 0-1</span><span>12 张素材</span><span>已成详情页</span></div>
            <p>健康提神咀嚼品品牌从产品定位、包装迭代、线下铺市到线上电商增长的项目案例。</p>
            <div class="proof-list">
              <div class="proof-line"><strong>证据</strong><span>产品包装、终端陈列、赛事展会、直播电商、复购系统。</span></div>
              <div class="proof-line"><strong>重点</strong><span>把消费品品牌从概念、内容、渠道到招商链路重新组织成案例。</span></div>
            </div>
            <a class="case-link" href="/me/projects/yikougege">查看案例</a>
          </article>
          <article class="project-card">
            <div class="small">BRAND PROJECT 02</div>
            <h3>可复美</h3>
            <div class="project-meta"><span>产品培训</span><span>14 张素材</span><span>已成详情页</span></div>
            <p>重组胶原蛋白产品培训、医学修护场景教育、药店门店和 O2O 动销承接的项目案例。</p>
            <div class="proof-list">
              <div class="proof-line"><strong>证据</strong><span>产品线、医院渠道、达人内容、明星素材、门店陈列、O2O 头图。</span></div>
              <div class="proof-line"><strong>重点</strong><span>把复杂产品讲义整理成店员能讲、用户能懂的培训系统。</span></div>
            </div>
            <a class="case-link" href="/me/projects/kefumei">查看案例</a>
          </article>
          <article class="project-card large">
            <div class="small">FEATURED PROJECT</div>
            <h3>Profile Site</h3>
            <div class="project-meta"><span>独立 Flask</span><span>/me 私密</span><span>已部署</span></div>
            <p>独立个人经历网站，使用登录保护、独立 cookie、SQLite 数据库、Gunicorn 服务和 Nginx 反向代理。</p>
            <div class="proof-list">
              <div class="proof-line"><strong>证据</strong><span>登录页、项目详情页、私密响应头、服务器服务与静态素材目录。</span></div>
              <div class="proof-line"><strong>重点</strong><span>作为长期个人档案库，承载项目、经历和私密资料。</span></div>
            </div>
          </article>
          <article class="project-card">
            <div class="small">DATA PRODUCT</div>
            <h3>数据工具平台</h3>
            <div class="project-meta"><span>工具系统</span><span>独立边界</span><span>待补案例</span></div>
            <p>记录产品数据、报表、竞品信息、价格体系等工具化工作，和个人站保持服务与数据边界。</p>
            <div class="proof-list">
              <div class="proof-line"><strong>证据</strong><span>后续补截图、数据流、自动化脚本和使用场景。</span></div>
              <div class="proof-line"><strong>重点</strong><span>展示把业务工作沉淀成工具和流程的能力。</span></div>
            </div>
          </article>
          <article class="project-card">
            <div class="small">KNOWLEDGE SYSTEM</div>
            <h3>个人知识与内容系统</h3>
            <div class="project-meta"><span>内容资产</span><span>长期沉淀</span><span>待补案例</span></div>
            <p>整理工作记录、反思、选题、音频、文章和可复用素材，形成长期内容资产。</p>
            <div class="proof-list">
              <div class="proof-line"><strong>证据</strong><span>后续补知识库结构、内容选题、复盘文章和输出记录。</span></div>
              <div class="proof-line"><strong>重点</strong><span>展示从经历到内容、从素材到系统的整理能力。</span></div>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="band dark" id="private">
      <div class="section-inner">
        <h2 class="section-title">私密资料，默认只给授权的人看。</h2>
        <p class="section-copy">这些内容默认只在登录后查看，不放到公开页面。后续可以加上传、下载、访客账号和后台编辑。</p>
        <div class="resource-grid">
          <article class="resource"><h3>简历与介绍文档</h3><p>放 PDF 简历、个人介绍、项目说明书和对外版本材料。</p></article>
          <article class="resource"><h3>图片与视频资料</h3><p>放生活照片、项目截图、演示视频、访谈或演讲素材。</p></article>
          <article class="resource"><h3>私密文章</h3><p>沉淀复盘、阶段总结、重要决策和不适合公开发布的内容。</p></article>
          <article class="resource"><h3>访客账号</h3><p>后续可以为朋友、合作方或招聘场景设置有限访问账号。</p></article>
        </div>
      </div>
    </section>
  </main>
  <footer class="footer-band">
    <div class="section-inner">/me · 当前为私密访问 · me_session 仅限 /me 路径</div>
  </footer>
  <script>
    (() => {
      const root = document.documentElement;
      const nav = document.querySelector(".nav");
      const heroMedia = document.querySelector(".hero-media");
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const updateScroll = () => {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const progress = Math.min(1, Math.max(0, window.scrollY / max));
        root.style.setProperty("--scroll", progress.toFixed(4));
        if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 12);
      };

      updateScroll();
      window.addEventListener("scroll", updateScroll, { passive: true });

      if (reduceMotion) return;

      root.classList.add("motion-ready");

      const revealItems = [
        ...document.querySelectorAll(".status-item, .band .section-title, .band .section-copy, .feature-card, .timeline-item, .project-card, .resource")
      ];

      revealItems.forEach((element, index) => {
        element.classList.add("reveal");
        element.style.setProperty("--delay", `${Math.min((index % 4) * 80, 240)}ms`);
      });

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });

      revealItems.forEach((element) => observer.observe(element));

      const timeline = document.querySelector(".timeline");
      const timelineItems = [...document.querySelectorAll(".timeline-item")];
      const updateTimeline = () => {
        if (!timeline || !timelineItems.length) return;
        const visible = timelineItems.filter((item) => item.classList.contains("is-visible")).length;
        timeline.style.setProperty("--timeline-progress", (visible / timelineItems.length).toFixed(3));
      };
      const timelineObserver = new MutationObserver(updateTimeline);
      timelineItems.forEach((item) => timelineObserver.observe(item, { attributes: true, attributeFilter: ["class"] }));

      let raf = 0;
      const moveGlow = (event) => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          root.style.setProperty("--pointer-x", `${event.clientX}px`);
          root.style.setProperty("--pointer-y", `${event.clientY}px`);

          if (heroMedia) {
            const rect = heroMedia.getBoundingClientRect();
            const x = (event.clientX - rect.left) / rect.width - 0.5;
            const y = (event.clientY - rect.top) / rect.height - 0.5;
            const inside = x > -0.7 && x < 0.7 && y > -0.7 && y < 0.7;
            root.style.setProperty("--hero-x", inside ? `${x * 14}px` : "0px");
            root.style.setProperty("--hero-y", inside ? `${y * 10}px` : "0px");
            root.style.setProperty("--hero-rx", inside ? `${y * -3}deg` : "0deg");
            root.style.setProperty("--hero-ry", inside ? `${x * 4}deg` : "0deg");
          }

          document.querySelectorAll(".feature-card, .project-card, .resource").forEach((card) => {
            const rect = card.getBoundingClientRect();
            const x = ((event.clientX - rect.left) / rect.width) * 100;
            const y = ((event.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty("--glow-x", `${x}%`);
            card.style.setProperty("--glow-y", `${y}%`);
          });
        });
      };

      window.addEventListener("pointermove", moveGlow, { passive: true });
      window.addEventListener("pointerleave", () => {
        root.style.setProperty("--hero-x", "0px");
        root.style.setProperty("--hero-y", "0px");
        root.style.setProperty("--hero-rx", "0deg");
        root.style.setProperty("--hero-ry", "0deg");
      });
    })();
  </script>
</body>
</html>
"""


YIKOU_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>益口葛葛项目案例</title>
  <style>
    * { box-sizing: border-box; }
    :root { color-scheme: light; --ink: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --bg: #f5f5f7; --paper: #fbfbfd; --panel: #fff; --blue: #0071e3; --green: #12805c; --amber: #b75f00; --dark: #121214; --scroll: 0; --pointer-x: 50vw; --pointer-y: 38vh; --tilt-x: 0deg; --tilt-y: 0deg; --lift-x: 0px; --lift-y: 0px; }
    html { scroll-behavior: smooth; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: var(--ink); background: var(--bg); }
    a { color: inherit; text-decoration: none; }
    img { display: block; max-width: 100%; }
    .scroll-progress { position: fixed; top: 0; left: 0; z-index: 70; width: 100%; height: 3px; background: linear-gradient(90deg, #0071e3, #12805c, #f5a623); transform: scaleX(var(--scroll)); transform-origin: left center; box-shadow: 0 0 20px rgba(0, 113, 227, .3); pointer-events: none; }
    .nav { position: sticky; top: 0; z-index: 40; border-bottom: 1px solid rgba(210, 210, 215, .72); background: rgba(251, 251, 253, .84); backdrop-filter: saturate(180%) blur(24px); transition: background .22s ease, box-shadow .22s ease; }
    .nav.is-scrolled { background: rgba(251, 251, 253, .94); box-shadow: 0 18px 44px rgba(29, 29, 31, .08); }
    .nav-inner { max-width: 1220px; min-height: 56px; margin: 0 auto; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 18px; }
    .brand { font-size: 14px; font-weight: 860; }
    .nav-links { display: flex; align-items: center; gap: 22px; color: #424245; font-size: 13px; }
    .nav-links a { transition: color .18s ease; }
    .nav-links a:hover { color: var(--blue); }
    .nav-status { display: flex; align-items: center; gap: 10px; color: #424245; font-size: 13px; white-space: nowrap; }
    .mode { color: var(--blue); font-weight: 850; }
    .logout, .back-link, .action { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 0 14px; border-radius: 8px; font-weight: 850; transition: transform .2s ease, background .2s ease, border-color .2s ease; }
    .logout, .back-link { border: 1px solid rgba(0, 113, 227, .22); color: var(--blue); background: rgba(255, 255, 255, .74); }
    main { overflow: hidden; }
    .section-inner { max-width: 1220px; margin: 0 auto; padding: 0 28px; }
    .hero { position: relative; padding: 58px 0 52px; background: var(--paper); }
    .hero-layout { display: grid; grid-template-columns: minmax(0, .92fr) minmax(520px, 1.08fr); gap: 38px; align-items: center; }
    .eyebrow { margin: 0 0 16px; color: var(--green); font-size: 13px; font-weight: 860; letter-spacing: 0; }
    h1 { max-width: 760px; margin: 0; font-size: 62px; line-height: 1.04; font-weight: 880; }
    .lead { max-width: 700px; margin: 22px 0 0; color: var(--muted); font-size: 20px; line-height: 1.6; }
    .meta-pills { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
    .pill { display: inline-flex; align-items: center; min-height: 34px; padding: 0 12px; border: 1px solid rgba(210, 210, 215, .9); border-radius: 999px; color: #424245; background: rgba(255, 255, 255, .72); font-size: 13px; font-weight: 800; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
    .action.primary { color: #fff; background: var(--blue); }
    .action.secondary { color: var(--blue); background: rgba(0, 113, 227, .08); }
    .hero-copy > * { animation: liftIn .72s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-copy h1 { animation-delay: .06s; }
    .hero-copy .lead { animation-delay: .14s; }
    .hero-copy .meta-pills { animation-delay: .2s; }
    .hero-copy .hero-actions { animation-delay: .26s; }
    .hero-visual { position: relative; perspective: 1200px; animation: imageIn .82s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-frame { position: relative; overflow: hidden; border: 1px solid rgba(210, 210, 215, .9); border-radius: 8px; background: #fff; box-shadow: 0 38px 84px rgba(29, 29, 31, .16); transform: translate3d(var(--lift-x), var(--lift-y), 0) rotateX(var(--tilt-x)) rotateY(var(--tilt-y)); transition: transform .16s ease-out, box-shadow .22s ease; will-change: transform; }
    .hero-frame::after { content: ""; position: absolute; inset: 0; background: linear-gradient(110deg, transparent 0 38%, rgba(255, 255, 255, .7) 49%, transparent 62%); transform: translateX(-95%); animation: sweep 6.2s ease-in-out infinite; pointer-events: none; }
    .hero-frame img { width: 100%; aspect-ratio: 1.22; object-fit: cover; }
    .caption-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin-top: 18px; border: 1px solid rgba(210, 210, 215, .86); border-radius: 8px; overflow: hidden; background: rgba(210, 210, 215, .86); }
    .caption-item { min-height: 92px; padding: 16px; background: rgba(255, 255, 255, .78); }
    .caption-label { color: var(--muted); font-size: 12px; font-weight: 820; }
    .caption-value { margin-top: 8px; font-size: 17px; line-height: 1.28; font-weight: 850; }
    .band { padding: 82px 0; background: var(--bg); }
    .band.paper { background: var(--paper); }
    .band.dark { color: #f5f5f7; background: var(--dark); }
    .band.dark .section-copy, .band.dark .small, .band.dark .work-card p, .band.dark .outcome-card p { color: #a1a1a6; }
    .section-head { display: grid; grid-template-columns: minmax(0, .9fr) minmax(360px, .55fr); gap: 30px; align-items: end; }
    .section-title { margin: 0; max-width: 760px; font-size: 46px; line-height: 1.08; font-weight: 870; }
    .section-copy { margin: 0; color: var(--muted); font-size: 18px; line-height: 1.68; }
    .work-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 36px; }
    .work-card { position: relative; overflow: hidden; isolation: isolate; min-height: 228px; padding: 24px; border: 1px solid rgba(210, 210, 215, .84); border-radius: 8px; background: var(--panel); box-shadow: 0 22px 56px rgba(29, 29, 31, .06); transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease; }
    .work-card::after, .outcome-card::after { content: ""; position: absolute; inset: 0; z-index: -1; opacity: 0; background: radial-gradient(460px circle at var(--glow-x, 50%) var(--glow-y, 20%), rgba(255, 255, 255, .9), transparent 42%); transition: opacity .28s ease; pointer-events: none; }
    .small { margin: 0 0 18px; color: var(--muted); font-size: 12px; font-weight: 850; }
    .work-card h3 { margin: 0 0 12px; font-size: 23px; line-height: 1.18; }
    .work-card p { margin: 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .story-stack { display: grid; gap: 74px; margin-top: 44px; }
    .story { display: grid; grid-template-columns: minmax(320px, .44fr) minmax(0, .56fr); gap: 34px; align-items: center; }
    .story:nth-child(even) { grid-template-columns: minmax(0, .56fr) minmax(320px, .44fr); }
    .story:nth-child(even) .story-copy { order: 2; }
    .story:nth-child(even) .media-grid { order: 1; }
    .story-copy h3 { margin: 0; font-size: 34px; line-height: 1.12; }
    .story-copy p { margin: 16px 0 0; color: var(--muted); font-size: 17px; line-height: 1.75; }
    .story-points { display: grid; gap: 12px; margin-top: 22px; }
    .story-point { padding-left: 14px; border-left: 2px solid rgba(0, 113, 227, .34); color: #424245; font-size: 15px; line-height: 1.65; }
    .media-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .media-tile { position: relative; overflow: hidden; border: 1px solid rgba(210, 210, 215, .86); border-radius: 8px; background: #fff; box-shadow: 0 20px 52px rgba(29, 29, 31, .08); }
    .media-tile.wide { grid-column: 1 / -1; }
    .media-tile img { width: 100%; aspect-ratio: 1.2; object-fit: cover; transition: transform .7s cubic-bezier(.2, .8, .2, 1); }
    .media-tile.wide img { aspect-ratio: 2.04; }
    .media-label { position: absolute; left: 12px; bottom: 12px; display: inline-flex; align-items: center; min-height: 30px; padding: 0 10px; border-radius: 8px; color: #fff; background: rgba(18, 18, 20, .58); backdrop-filter: blur(18px); font-size: 12px; font-weight: 850; }
    .system-panel { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; margin-top: 36px; }
    .system-visual { overflow: hidden; border: 1px solid rgba(245, 245, 247, .18); border-radius: 8px; background: rgba(255, 255, 255, .08); }
    .system-visual img { width: 100%; aspect-ratio: 1.4; object-fit: cover; }
    .system-copy { display: grid; align-content: center; gap: 14px; padding: 30px; border: 1px solid rgba(245, 245, 247, .16); border-radius: 8px; background: rgba(255, 255, 255, .07); }
    .system-copy h3 { margin: 0; font-size: 30px; line-height: 1.14; }
    .system-copy p { margin: 0; color: #a1a1a6; font-size: 16px; line-height: 1.72; }
    .outcome-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 36px; }
    .outcome-card { position: relative; overflow: hidden; isolation: isolate; min-height: 190px; padding: 22px; border: 1px solid rgba(210, 210, 215, .84); border-radius: 8px; background: var(--panel); box-shadow: 0 18px 48px rgba(29, 29, 31, .055); transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease; }
    .outcome-card h3 { margin: 0 0 10px; font-size: 20px; line-height: 1.2; }
    .outcome-card p { margin: 0; color: var(--muted); font-size: 14px; line-height: 1.66; }
    .closing { padding: 48px 0 56px; background: var(--paper); }
    .closing-inner { max-width: 1220px; margin: 0 auto; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 18px; color: var(--muted); font-size: 13px; }
    .motion-ready .reveal { opacity: 0; transform: translateY(34px); filter: blur(10px); transition: opacity .78s cubic-bezier(.2, .8, .2, 1), transform .78s cubic-bezier(.2, .8, .2, 1), filter .78s ease; transition-delay: var(--delay, 0ms); }
    .motion-ready .reveal.is-visible { opacity: 1; transform: translateY(0); filter: blur(0); }
    @media (hover: hover) {
      .logout:hover, .back-link:hover, .action:hover { transform: translateY(-1px); }
      .work-card:hover, .outcome-card:hover { transform: translateY(-6px); border-color: rgba(0, 113, 227, .28); box-shadow: 0 30px 72px rgba(29, 29, 31, .12); }
      .work-card:hover::after, .outcome-card:hover::after { opacity: .48; }
      .media-tile:hover img { transform: scale(1.035); }
    }
    @keyframes liftIn { from { opacity: 0; transform: translateY(24px); filter: blur(8px); } to { opacity: 1; transform: translateY(0); filter: blur(0); } }
    @keyframes imageIn { from { opacity: 0; transform: translateY(28px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes sweep { 0%, 35% { opacity: 0; transform: translateX(-95%); } 50% { opacity: .76; } 74%, 100% { opacity: 0; transform: translateX(95%); } }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      .scroll-progress { display: none; }
      .hero-copy > *, .hero-visual, .hero-frame, .hero-frame::after, .media-tile img, .reveal, .work-card, .outcome-card { animation: none; transition: none; transform: none; filter: none; opacity: 1; }
    }
    @media (max-width: 1060px) {
      .nav-inner { align-items: flex-start; flex-direction: column; padding: 13px 18px; }
      .nav-links { width: 100%; gap: 16px; overflow-x: auto; padding-bottom: 3px; }
      .nav-status { width: 100%; justify-content: space-between; }
      .section-inner, .closing-inner { padding: 0 18px; }
      .hero { padding: 38px 0 36px; }
      .hero-layout, .section-head, .story, .story:nth-child(even), .system-panel { grid-template-columns: 1fr; }
      .story:nth-child(even) .story-copy, .story:nth-child(even) .media-grid { order: initial; }
      h1 { font-size: 42px; }
      .lead { font-size: 17px; }
      .section-title { font-size: 34px; }
      .story-copy h3 { font-size: 28px; }
      .work-grid, .outcome-grid { grid-template-columns: 1fr; }
      .caption-row { grid-template-columns: 1fr; }
      .band { padding: 58px 0; }
      .closing-inner { align-items: flex-start; flex-direction: column; }
    }
    @media (max-width: 640px) {
      .media-grid { grid-template-columns: 1fr; }
      .media-tile.wide { grid-column: auto; }
      .media-tile.wide img, .media-tile img { aspect-ratio: 1.18; }
      .nav-links { font-size: 12px; }
      .nav-status { flex-wrap: wrap; }
    }
  </style>
</head>
<body>
  <div class="scroll-progress" aria-hidden="true"></div>
  <header class="nav">
    <div class="nav-inner">
      <a class="brand" href="/me/">sososong / private profile</a>
      <nav class="nav-links" aria-label="项目导航">
        <a href="#work">工作拆解</a>
        <a href="#story">项目呈现</a>
        <a href="#system">增长系统</a>
        <a href="#outcome">沉淀结果</a>
      </nav>
      <div class="nav-status"><span>当前登录：{{ username }}</span><span class="mode">私密模式</span><a class="logout" href="/me/logout">退出</a></div>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="section-inner">
        <div class="hero-layout">
          <div class="hero-copy">
            <p class="eyebrow">BRAND 0-1 CASE / 益口葛葛</p>
            <h1>从产品概念到渠道增长的健康提神咀嚼品牌搭建。</h1>
            <p class="lead">以年轻人提神和咀嚼替代场景为切入点，把产品卖点、包装表达、线下触点、内容矩阵、电商转化和经销商招商串成一套可落地的增长工程。</p>
            <div class="meta-pills" aria-label="项目关键词">
              <span class="pill">品牌从 0 到 1</span>
              <span class="pill">产品迭代</span>
              <span class="pill">线下铺市</span>
              <span class="pill">新媒体矩阵</span>
              <span class="pill">招商转化</span>
              <span class="pill">团队培训</span>
            </div>
            <div class="hero-actions">
              <a class="action primary" href="#story">查看呈现</a>
              <a class="action secondary" href="/me/">返回首页</a>
            </div>
          </div>
          <div class="hero-visual">
            <div class="hero-frame">
              <img src="{{ url_for('static', filename='projects/yikougege/assets/product-family.jpg') }}" alt="益口葛葛产品组合展示" />
            </div>
          </div>
        </div>
        <div class="caption-row" aria-label="案例范围">
          <div class="caption-item"><div class="caption-label">项目角色</div><div class="caption-value">品牌与增长体系搭建</div></div>
          <div class="caption-item"><div class="caption-label">核心资产</div><div class="caption-value">产品、包装、内容、渠道素材</div></div>
          <div class="caption-item"><div class="caption-label">呈现方式</div><div class="caption-value">私密案例页重排版</div></div>
        </div>
      </div>
    </section>

    <section class="band paper" id="work">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">把一份项目介绍，拆成可读的能力证据。</h2>
          <p class="section-copy">这里不按原 PDF 页序复刻，而是按实际工作流重组：先讲清品牌方向，再展示产品与渠道动作，最后沉淀增长机制和团队打法。</p>
        </div>
        <div class="work-grid">
          <article class="work-card"><p class="small">01 / POSITIONING</p><h3>定位与品牌系统</h3><p>把“提神、咀嚼、健康替代”放到统一表达里，形成名称、视觉、口号、阶段传播和线下物料的基础框架。</p></article>
          <article class="work-card"><p class="small">02 / PRODUCT STORY</p><h3>技术卖点转译</h3><p>围绕葛根纤维、青果基底风味和植物能量提取等信息，把研发语言转成消费者能理解的产品理由。</p></article>
          <article class="work-card"><p class="small">03 / RETAIL</p><h3>渠道与终端触点</h3><p>把陈列、试吃、赛事、展会、商圈和交通广告组织成一个可反复触达用户的线下网络。</p></article>
          <article class="work-card"><p class="small">04 / CONTENT</p><h3>内容与电商承接</h3><p>用新媒体矩阵、直播、自播、电商货架和短视频素材承接认知，把“看见”转到“购买”。</p></article>
          <article class="work-card"><p class="small">05 / RETENTION</p><h3>复购激励机制</h3><p>通过扫码红包和门店店员激励，把消费者复购和终端推荐连接起来，强化动销和留存。</p></article>
          <article class="work-card"><p class="small">06 / DEALER GROWTH</p><h3>招商与团队复制</h3><p>把广告曝光、线索收集、商务跟进、经销商大会和区域培训形成一条 B 端增长链路。</p></article>
        </div>
      </div>
    </section>

    <section class="band" id="story">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">项目呈现从产品开始，再进入场景。</h2>
          <p class="section-copy">筛选 PDF 中最能说明问题的素材，保留真实图像证据，同时重新组织版面节奏和叙事层级。</p>
        </div>
        <div class="story-stack">
          <section class="story">
            <div class="story-copy">
              <h3>产品与包装：先让新品像一个完整品牌。</h3>
              <p>早期重点不是堆满卖点，而是让用户在几秒内理解这是什么、适合什么场景、为什么可以替代原有咀嚼习惯。</p>
              <div class="story-points">
                <div class="story-point">包装系统兼顾货架识别和口味区分，先建立“看得懂”的购买入口。</div>
                <div class="story-point">产品迭代围绕口感、风味、规格和视觉统一度推进，减少新品教育成本。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/yikougege/assets/packaging-system.jpg') }}" alt="益口葛葛包装系统" /><figcaption class="media-label">包装系统</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/product-iteration.jpg') }}" alt="益口葛葛产品迭代" /><figcaption class="media-label">产品迭代</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/retail-display.jpg') }}" alt="益口葛葛终端陈列" /><figcaption class="media-label">终端陈列</figcaption></figure>
            </div>
          </section>

          <section class="story">
            <div class="story-copy">
              <h3>线下启动：用真实触点建立信任。</h3>
              <p>项目把线下当成品牌冷启动的主战场：能试吃、能看见、能接触销售人员，也能在展会和赛事里获得更强的场景感。</p>
              <div class="story-points">
                <div class="story-point">赛事、展会和门店铺市负责让新品进入真实人群和真实货架。</div>
                <div class="story-point">户外与交通场景广告负责做连续曝光，让招商和零售都更容易被理解。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/sports-scene.jpg') }}" alt="益口葛葛赛事场景" /><figcaption class="media-label">赛事触点</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/trade-show.jpg') }}" alt="益口葛葛展会现场" /><figcaption class="media-label">展会招商</figcaption></figure>
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/yikougege/assets/media-placement.jpg') }}" alt="益口葛葛线下广告投放" /><figcaption class="media-label">线下广告</figcaption></figure>
            </div>
          </section>

          <section class="story">
            <div class="story-copy">
              <h3>线上承接：把认知流量变成购买路径。</h3>
              <p>线上部分承担两个任务：让用户反复看到新品的使用理由，也让已经被种草的人可以直接进入电商、直播或私域转化。</p>
              <div class="story-points">
                <div class="story-point">内容矩阵覆盖品牌介绍、场景教育、口味展示和活动承接。</div>
                <div class="story-point">电商与直播把流量承接为可购买、可复购、可追踪的交易动作。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/yikougege/assets/content-matrix.jpg') }}" alt="益口葛葛内容矩阵" /><figcaption class="media-label">内容矩阵</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/ecommerce-grid.jpg') }}" alt="益口葛葛电商货架" /><figcaption class="media-label">电商货架</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/yikougege/assets/live-commerce.jpg') }}" alt="益口葛葛直播电商" /><figcaption class="media-label">直播转化</figcaption></figure>
            </div>
          </section>
        </div>
      </div>
    </section>

    <section class="band dark" id="system">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">增长不是单点动作，而是一套可复制系统。</h2>
          <p class="section-copy">复购激励、门店推荐、招商线索和区域培训放在同一个框架里，才能把一次传播变成长期运转。</p>
        </div>
        <div class="system-panel">
          <div class="system-visual"><img src="{{ url_for('static', filename='projects/yikougege/assets/red-packet-system.jpg') }}" alt="益口葛葛扫码红包系统" /></div>
          <div class="system-copy">
            <h3>扫码红包把用户和门店都纳入增长闭环。</h3>
            <p>消费者扫码获得即时反馈，店员扫码获得推荐激励，品牌则得到更清晰的动销触点和复购入口。</p>
          </div>
          <div class="system-copy">
            <h3>招商之后，还需要训练可复制打法。</h3>
            <p>区域团队培训、经销商会议和标准化物料，让不同城市、不同渠道可以围绕同一套项目语言推进。</p>
          </div>
          <div class="system-visual"><img src="{{ url_for('static', filename='projects/yikougege/assets/training-room.jpg') }}" alt="益口葛葛区域团队培训" /></div>
        </div>
      </div>
    </section>

    <section class="band paper" id="outcome">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">最终沉淀为四类可复用资产。</h2>
          <p class="section-copy">不虚构硬数据，只保留从素材中能验证的项目成果类型，方便后续补充真实指标和复盘细节。</p>
        </div>
        <div class="outcome-grid">
          <article class="outcome-card"><h3>品牌表达资产</h3><p>完成从产品概念、视觉识别、包装体系到宣传物料的一体化表达。</p></article>
          <article class="outcome-card"><h3>线下启动打法</h3><p>形成铺市陈列、试吃活动、赛事展会和户外广告组合，用真实场景建立认知。</p></article>
          <article class="outcome-card"><h3>线上转化链路</h3><p>搭建内容矩阵、电商货架、自播场景和复购激励，让流量有承接路径。</p></article>
          <article class="outcome-card"><h3>招商复制能力</h3><p>沉淀线索获取、商务跟进、经销商会议和区域团队培训的协同流程。</p></article>
        </div>
      </div>
    </section>
  </main>

  <footer class="closing">
    <div class="closing-inner">
      <div>/me 路径下的私密项目案例 · me_session 仅限 /me 路径</div>
      <a class="back-link" href="/me/">返回个人首页</a>
    </div>
  </footer>

  <script>
    (() => {
      const root = document.documentElement;
      const nav = document.querySelector(".nav");
      const heroVisual = document.querySelector(".hero-visual");
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const updateScroll = () => {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const progress = Math.min(1, Math.max(0, window.scrollY / max));
        root.style.setProperty("--scroll", progress.toFixed(4));
        if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 12);
      };

      updateScroll();
      window.addEventListener("scroll", updateScroll, { passive: true });

      if (reduceMotion) return;

      root.classList.add("motion-ready");

      const revealItems = [
        ...document.querySelectorAll(".caption-item, .section-title, .section-copy, .work-card, .story, .media-tile, .system-visual, .system-copy, .outcome-card")
      ];

      revealItems.forEach((element, index) => {
        element.classList.add("reveal");
        element.style.setProperty("--delay", `${Math.min((index % 5) * 70, 280)}ms`);
      });

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });

      revealItems.forEach((element) => observer.observe(element));

      let raf = 0;
      const moveGlow = (event) => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          if (heroVisual) {
            const rect = heroVisual.getBoundingClientRect();
            const x = (event.clientX - rect.left) / rect.width - 0.5;
            const y = (event.clientY - rect.top) / rect.height - 0.5;
            const inside = x > -0.7 && x < 0.7 && y > -0.7 && y < 0.7;
            root.style.setProperty("--lift-x", inside ? `${x * 14}px` : "0px");
            root.style.setProperty("--lift-y", inside ? `${y * 10}px` : "0px");
            root.style.setProperty("--tilt-x", inside ? `${y * -3}deg` : "0deg");
            root.style.setProperty("--tilt-y", inside ? `${x * 4}deg` : "0deg");
          }

          document.querySelectorAll(".work-card, .outcome-card").forEach((card) => {
            const rect = card.getBoundingClientRect();
            const x = ((event.clientX - rect.left) / rect.width) * 100;
            const y = ((event.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty("--glow-x", `${x}%`);
            card.style.setProperty("--glow-y", `${y}%`);
          });
        });
      };

      window.addEventListener("pointermove", moveGlow, { passive: true });
      window.addEventListener("pointerleave", () => {
        root.style.setProperty("--lift-x", "0px");
        root.style.setProperty("--lift-y", "0px");
        root.style.setProperty("--tilt-x", "0deg");
        root.style.setProperty("--tilt-y", "0deg");
      });
    })();
  </script>
</body>
</html>
"""


KEFUMEI_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>可复美项目案例</title>
  <style>
    * { box-sizing: border-box; }
    :root { color-scheme: light; --ink: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --bg: #f5f7f8; --paper: #fbfbfd; --panel: #fff; --blue: #0071e3; --teal: #007f8f; --mint: #14a77b; --amber: #b86900; --dark: #121416; --scroll: 0; --lift-x: 0px; --lift-y: 0px; --tilt-x: 0deg; --tilt-y: 0deg; }
    html { scroll-behavior: smooth; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: var(--ink); background: var(--bg); }
    a { color: inherit; text-decoration: none; }
    img { display: block; max-width: 100%; }
    .scroll-progress { position: fixed; top: 0; left: 0; z-index: 70; width: 100%; height: 3px; background: linear-gradient(90deg, #0071e3, #14a77b, #b86900); transform: scaleX(var(--scroll)); transform-origin: left center; box-shadow: 0 0 20px rgba(0, 113, 227, .28); pointer-events: none; }
    .nav { position: sticky; top: 0; z-index: 40; border-bottom: 1px solid rgba(210, 210, 215, .72); background: rgba(251, 251, 253, .86); backdrop-filter: saturate(180%) blur(24px); transition: background .22s ease, box-shadow .22s ease; }
    .nav.is-scrolled { background: rgba(251, 251, 253, .95); box-shadow: 0 18px 44px rgba(29, 29, 31, .08); }
    .nav-inner { max-width: 1220px; min-height: 56px; margin: 0 auto; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 18px; }
    .brand { font-size: 14px; font-weight: 860; }
    .nav-links { display: flex; align-items: center; gap: 22px; color: #424245; font-size: 13px; }
    .nav-links a:hover { color: var(--blue); }
    .nav-status { display: flex; align-items: center; gap: 10px; color: #424245; font-size: 13px; white-space: nowrap; }
    .mode { color: var(--blue); font-weight: 850; }
    .logout, .back-link, .action { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 0 14px; border-radius: 8px; font-weight: 850; transition: transform .2s ease, background .2s ease, border-color .2s ease; }
    .logout, .back-link { border: 1px solid rgba(0, 113, 227, .22); color: var(--blue); background: rgba(255, 255, 255, .74); }
    main { overflow: hidden; }
    .section-inner { max-width: 1220px; margin: 0 auto; padding: 0 28px; }
    .hero { position: relative; padding: 58px 0 52px; background: var(--paper); }
    .hero-layout { display: grid; grid-template-columns: minmax(0, .9fr) minmax(520px, 1.1fr); gap: 38px; align-items: center; }
    .eyebrow { margin: 0 0 16px; color: var(--teal); font-size: 13px; font-weight: 860; letter-spacing: 0; }
    h1 { max-width: 760px; margin: 0; font-size: 60px; line-height: 1.04; font-weight: 880; }
    .lead { max-width: 690px; margin: 22px 0 0; color: var(--muted); font-size: 20px; line-height: 1.6; }
    .meta-pills { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
    .pill { display: inline-flex; align-items: center; min-height: 34px; padding: 0 12px; border: 1px solid rgba(210, 210, 215, .9); border-radius: 999px; color: #424245; background: rgba(255, 255, 255, .72); font-size: 13px; font-weight: 800; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
    .action.primary { color: #fff; background: var(--blue); }
    .action.secondary { color: var(--blue); background: rgba(0, 113, 227, .08); }
    .hero-copy > * { animation: liftIn .72s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-copy h1 { animation-delay: .06s; }
    .hero-copy .lead { animation-delay: .14s; }
    .hero-copy .meta-pills { animation-delay: .2s; }
    .hero-copy .hero-actions { animation-delay: .26s; }
    .hero-visual { position: relative; perspective: 1200px; animation: imageIn .82s cubic-bezier(.2, .8, .2, 1) both; }
    .hero-frame { position: relative; overflow: hidden; border: 1px solid rgba(210, 210, 215, .9); border-radius: 8px; background: #fff; box-shadow: 0 38px 84px rgba(29, 29, 31, .14); transform: translate3d(var(--lift-x), var(--lift-y), 0) rotateX(var(--tilt-x)) rotateY(var(--tilt-y)); transition: transform .16s ease-out; will-change: transform; }
    .hero-frame::after { content: ""; position: absolute; inset: 0; background: linear-gradient(110deg, transparent 0 38%, rgba(255, 255, 255, .62) 49%, transparent 62%); transform: translateX(-95%); animation: sweep 6.2s ease-in-out infinite; pointer-events: none; }
    .hero-frame img { width: 100%; aspect-ratio: 1.78; object-fit: cover; }
    .caption-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin-top: 18px; border: 1px solid rgba(210, 210, 215, .86); border-radius: 8px; overflow: hidden; background: rgba(210, 210, 215, .86); }
    .caption-item { min-height: 92px; padding: 16px; background: rgba(255, 255, 255, .78); }
    .caption-label { color: var(--muted); font-size: 12px; font-weight: 820; }
    .caption-value { margin-top: 8px; font-size: 17px; line-height: 1.28; font-weight: 850; }
    .band { padding: 82px 0; background: var(--bg); }
    .band.paper { background: var(--paper); }
    .band.dark { color: #f5f5f7; background: var(--dark); }
    .band.dark .section-copy, .band.dark .small, .band.dark .work-card p, .band.dark .outcome-card p { color: #a1a1a6; }
    .section-head { display: grid; grid-template-columns: minmax(0, .9fr) minmax(360px, .55fr); gap: 30px; align-items: end; }
    .section-title { margin: 0; max-width: 760px; font-size: 46px; line-height: 1.08; font-weight: 870; }
    .section-copy { margin: 0; color: var(--muted); font-size: 18px; line-height: 1.68; }
    .work-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 36px; }
    .work-card { position: relative; overflow: hidden; isolation: isolate; min-height: 228px; padding: 24px; border: 1px solid rgba(210, 210, 215, .84); border-radius: 8px; background: var(--panel); box-shadow: 0 22px 56px rgba(29, 29, 31, .055); transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease; }
    .work-card::after, .outcome-card::after { content: ""; position: absolute; inset: 0; z-index: -1; opacity: 0; background: radial-gradient(460px circle at var(--glow-x, 50%) var(--glow-y, 20%), rgba(255, 255, 255, .92), transparent 42%); transition: opacity .28s ease; pointer-events: none; }
    .small { margin: 0 0 18px; color: var(--muted); font-size: 12px; font-weight: 850; }
    .work-card h3 { margin: 0 0 12px; font-size: 23px; line-height: 1.18; }
    .work-card p { margin: 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .story-stack { display: grid; gap: 74px; margin-top: 44px; }
    .story { display: grid; grid-template-columns: minmax(320px, .44fr) minmax(0, .56fr); gap: 34px; align-items: center; }
    .story:nth-child(even) { grid-template-columns: minmax(0, .56fr) minmax(320px, .44fr); }
    .story:nth-child(even) .story-copy { order: 2; }
    .story:nth-child(even) .media-grid { order: 1; }
    .story-copy h3 { margin: 0; font-size: 34px; line-height: 1.12; }
    .story-copy p { margin: 16px 0 0; color: var(--muted); font-size: 17px; line-height: 1.75; }
    .story-points { display: grid; gap: 12px; margin-top: 22px; }
    .story-point { padding-left: 14px; border-left: 2px solid rgba(0, 127, 143, .34); color: #424245; font-size: 15px; line-height: 1.65; }
    .media-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .media-tile { position: relative; overflow: hidden; border: 1px solid rgba(210, 210, 215, .86); border-radius: 8px; background: #fff; box-shadow: 0 20px 52px rgba(29, 29, 31, .08); }
    .media-tile.wide { grid-column: 1 / -1; }
    .media-tile img { width: 100%; aspect-ratio: 1.2; object-fit: cover; transition: transform .7s cubic-bezier(.2, .8, .2, 1); }
    .media-tile.wide img { aspect-ratio: 2.05; }
    .media-label { position: absolute; left: 12px; bottom: 12px; display: inline-flex; align-items: center; min-height: 30px; padding: 0 10px; border-radius: 8px; color: #fff; background: rgba(18, 20, 22, .58); backdrop-filter: blur(18px); font-size: 12px; font-weight: 850; }
    .system-panel { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; margin-top: 36px; }
    .system-visual { overflow: hidden; border: 1px solid rgba(245, 245, 247, .18); border-radius: 8px; background: rgba(255, 255, 255, .08); }
    .system-visual img { width: 100%; aspect-ratio: 1.55; object-fit: cover; }
    .system-copy { display: grid; align-content: center; gap: 14px; padding: 30px; border: 1px solid rgba(245, 245, 247, .16); border-radius: 8px; background: rgba(255, 255, 255, .07); }
    .system-copy h3 { margin: 0; font-size: 30px; line-height: 1.14; }
    .system-copy p { margin: 0; color: #a1a1a6; font-size: 16px; line-height: 1.72; }
    .outcome-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 36px; }
    .outcome-card { position: relative; overflow: hidden; isolation: isolate; min-height: 190px; padding: 22px; border: 1px solid rgba(210, 210, 215, .84); border-radius: 8px; background: var(--panel); box-shadow: 0 18px 48px rgba(29, 29, 31, .055); transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease; }
    .outcome-card h3 { margin: 0 0 10px; font-size: 20px; line-height: 1.2; }
    .outcome-card p { margin: 0; color: var(--muted); font-size: 14px; line-height: 1.66; }
    .closing { padding: 48px 0 56px; background: var(--paper); }
    .closing-inner { max-width: 1220px; margin: 0 auto; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 18px; color: var(--muted); font-size: 13px; }
    .motion-ready .reveal { opacity: 0; transform: translateY(34px); filter: blur(10px); transition: opacity .78s cubic-bezier(.2, .8, .2, 1), transform .78s cubic-bezier(.2, .8, .2, 1), filter .78s ease; transition-delay: var(--delay, 0ms); }
    .motion-ready .reveal.is-visible { opacity: 1; transform: translateY(0); filter: blur(0); }
    @media (hover: hover) {
      .logout:hover, .back-link:hover, .action:hover { transform: translateY(-1px); }
      .work-card:hover, .outcome-card:hover { transform: translateY(-6px); border-color: rgba(0, 127, 143, .28); box-shadow: 0 30px 72px rgba(29, 29, 31, .12); }
      .work-card:hover::after, .outcome-card:hover::after { opacity: .48; }
      .media-tile:hover img { transform: scale(1.035); }
    }
    @keyframes liftIn { from { opacity: 0; transform: translateY(24px); filter: blur(8px); } to { opacity: 1; transform: translateY(0); filter: blur(0); } }
    @keyframes imageIn { from { opacity: 0; transform: translateY(28px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes sweep { 0%, 35% { opacity: 0; transform: translateX(-95%); } 50% { opacity: .76; } 74%, 100% { opacity: 0; transform: translateX(95%); } }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      .scroll-progress { display: none; }
      .hero-copy > *, .hero-visual, .hero-frame, .hero-frame::after, .media-tile img, .reveal, .work-card, .outcome-card { animation: none; transition: none; transform: none; filter: none; opacity: 1; }
    }
    @media (max-width: 1060px) {
      .nav-inner { align-items: flex-start; flex-direction: column; padding: 13px 18px; }
      .nav-links { width: 100%; gap: 16px; overflow-x: auto; padding-bottom: 3px; }
      .nav-status { width: 100%; justify-content: space-between; }
      .section-inner, .closing-inner { padding: 0 18px; }
      .hero { padding: 38px 0 36px; }
      .hero-layout, .section-head, .story, .story:nth-child(even), .system-panel { grid-template-columns: 1fr; }
      .story:nth-child(even) .story-copy, .story:nth-child(even) .media-grid { order: initial; }
      h1 { font-size: 42px; }
      .lead { font-size: 17px; }
      .section-title { font-size: 34px; }
      .story-copy h3 { font-size: 28px; }
      .work-grid, .outcome-grid { grid-template-columns: 1fr; }
      .caption-row { grid-template-columns: 1fr; }
      .band { padding: 58px 0; }
      .closing-inner { align-items: flex-start; flex-direction: column; }
    }
    @media (max-width: 640px) {
      .media-grid { grid-template-columns: 1fr; }
      .media-tile.wide { grid-column: auto; }
      .media-tile.wide img, .media-tile img { aspect-ratio: 1.18; }
      .nav-links { font-size: 12px; }
      .nav-status { flex-wrap: wrap; }
    }
  </style>
</head>
<body>
  <div class="scroll-progress" aria-hidden="true"></div>
  <header class="nav">
    <div class="nav-inner">
      <a class="brand" href="/me/">sososong / private profile</a>
      <nav class="nav-links" aria-label="项目导航">
        <a href="#work">工作拆解</a>
        <a href="#product">产品系统</a>
        <a href="#channel">渠道内容</a>
        <a href="#retail">门店动销</a>
        <a href="#outcome">沉淀结果</a>
      </nav>
      <div class="nav-status"><span>当前登录：{{ username }}</span><span class="mode">私密模式</span><a class="logout" href="/me/logout">退出</a></div>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="section-inner">
        <div class="hero-layout">
          <div class="hero-copy">
            <p class="eyebrow">BRAND PROJECT 02 / 可复美</p>
            <h1>把医学修护产品，讲成门店能卖、用户能懂的培训系统。</h1>
            <p class="lead">基于两份产品培训材料，重新整理可复美的技术背书、产品组合、临床证据、内容传播和药店/O2O 动销动作，形成一个更适合项目展示的案例页。</p>
            <div class="meta-pills" aria-label="项目关键词">
              <span class="pill">重组胶原蛋白</span>
              <span class="pill">产品培训</span>
              <span class="pill">医学修护场景</span>
              <span class="pill">药店渠道</span>
              <span class="pill">达人内容</span>
              <span class="pill">O2O 承接</span>
            </div>
            <div class="hero-actions">
              <a class="action primary" href="#product">查看产品系统</a>
              <a class="action secondary" href="/me/">返回首页</a>
            </div>
          </div>
          <div class="hero-visual">
            <div class="hero-frame">
              <img src="{{ url_for('static', filename='projects/kefumei/assets/brand-lineup.jpg') }}" alt="可复美产品线展示" />
            </div>
          </div>
        </div>
        <div class="caption-row" aria-label="案例范围">
          <div class="caption-item"><div class="caption-label">项目位置</div><div class="caption-value">第二个品牌项目案例</div></div>
          <div class="caption-item"><div class="caption-label">素材来源</div><div class="caption-value">产品讲义与培训材料重组</div></div>
          <div class="caption-item"><div class="caption-label">呈现原则</div><div class="caption-value">保留证据，不照搬原文</div></div>
        </div>
      </div>
    </section>

    <section class="band paper" id="work">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">从一套培训资料里，拆出可展示的项目能力。</h2>
          <p class="section-copy">原材料信息量很大，我按“讲清为什么可信、讲清怎么使用、讲清怎么卖、讲清怎么复制”四个层级重排。</p>
        </div>
        <div class="work-grid">
          <article class="work-card"><p class="small">01 / TRUST</p><h3>技术背书转译</h3><p>把巨子生物、重组胶原蛋白、医院渠道和安全性材料，压缩成消费者和店员都能理解的信任基础。</p></article>
          <article class="work-card"><p class="small">02 / PRODUCT</p><h3>三类产品培训</h3><p>把敷料、喷雾、修复乳分别对应深度修护、外出即时修护和日常持续保湿场景，降低推荐门槛。</p></article>
          <article class="work-card"><p class="small">03 / SCENARIO</p><h3>问题肌肤场景</h3><p>围绕敏感、痘痘、医美术后、干痒泛红等材料线索，把产品功能转为更自然的使用场景。</p></article>
          <article class="work-card"><p class="small">04 / CONTENT</p><h3>内容与达人证据</h3><p>整合达人、明星、平台内容与品牌传播截图，把“听说过”转成可被反复使用的内容资产。</p></article>
          <article class="work-card"><p class="small">05 / RETAIL</p><h3>药店与 O2O 动销</h3><p>把陈列、门店推荐、O2O 头图、五星保真和 IP 联名活动组织成线下线上同步承接。</p></article>
          <article class="work-card"><p class="small">06 / ENABLEMENT</p><h3>销售培训复制</h3><p>把复杂功效、使用方法、竞品差异和常见问题，整理为店员可复述、可开口、可成交的培训脚本。</p></article>
        </div>
      </div>
    </section>

    <section class="band" id="product">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">先建立信任，再把产品系统讲清楚。</h2>
          <p class="section-copy">案例页不直接复制讲义内容，而是把技术、产品和使用场景重新排成一条更顺的培训逻辑。</p>
        </div>
        <div class="story-stack">
          <section class="story">
            <div class="story-copy">
              <h3>技术和渠道背书，是专业产品的第一层信任。</h3>
              <p>讲义里的企业、医院、渠道和达人信息很分散。重排后先让读者知道品牌为什么有专业基础，再进入产品卖点。</p>
              <div class="story-points">
                <div class="story-point">用重组胶原蛋白、医疗器械资质和医院渠道覆盖，建立“专业修护”的理解框架。</div>
                <div class="story-point">达人和明星内容不作为堆砌素材，而是作为品牌认知和内容资产的证据层。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/kefumei/assets/device-sheet.jpg') }}" alt="可复美医疗器械敷料产品" /><figcaption class="media-label">产品定位</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/medical-channel-map.jpg') }}" alt="可复美医院渠道覆盖" /><figcaption class="media-label">医院渠道</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/kol-education-matrix.jpg') }}" alt="可复美达人内容矩阵" /><figcaption class="media-label">达人教育</figcaption></figure>
            </div>
          </section>

          <section class="story">
            <div class="story-copy">
              <h3>三件产品，对应三个不同的修护时刻。</h3>
              <p>把产品训练从“背参数”改成“懂场景”：敷料做深度修护，喷雾做外出即时舒缓，修复乳做日常持续保湿和屏障维护。</p>
              <div class="story-points">
                <div class="story-point">产品线被组织成可推荐的组合，而不是孤立 SKU。</div>
                <div class="story-point">每个产品都保留“适用人群、使用时机、推荐话术”的培训入口。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/kefumei/assets/three-product-system.jpg') }}" alt="可复美三产品组合" /><figcaption class="media-label">三产品系统</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/sheet-product.jpg') }}" alt="可复美敷料产品" /><figcaption class="media-label">敷料</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/spray-product.jpg') }}" alt="可复美喷雾产品" /><figcaption class="media-label">喷雾</figcaption></figure>
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/kefumei/assets/lotion-product.jpg') }}" alt="可复美修复乳产品" /><figcaption class="media-label">修复乳</figcaption></figure>
            </div>
          </section>
        </div>
      </div>
    </section>

    <section class="band paper" id="channel">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">内容传播和渠道承接，要连成一条线。</h2>
          <p class="section-copy">可复美材料里既有专业证据，也有明星达人、双 11 复盘和综艺联名。这里把它们重排为“认知 - 触达 - 转化”的项目链路。</p>
        </div>
        <div class="story-stack">
          <section class="story">
            <div class="story-copy">
              <h3>线上负责教育和种草，线下负责看见和成交。</h3>
              <p>对于高认知但高解释成本的产品，内容和渠道不能分开看。达人内容降低理解成本，药店陈列和 O2O 页面把兴趣承接到购买动作。</p>
              <div class="story-points">
                <div class="story-point">明星达人素材服务于信任和话题，不替代产品知识本身。</div>
                <div class="story-point">O2O 头图、门店陈列和联名活动，让线上流量和线下推荐有统一的视觉锚点。</div>
              </div>
            </div>
            <div class="media-grid">
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/celebrity-grid.jpg') }}" alt="可复美明星推荐素材" /><figcaption class="media-label">明星内容</figcaption></figure>
              <figure class="media-tile"><img src="{{ url_for('static', filename='projects/kefumei/assets/campaign-recap.jpg') }}" alt="可复美内容活动复盘" /><figcaption class="media-label">活动复盘</figcaption></figure>
              <figure class="media-tile wide"><img src="{{ url_for('static', filename='projects/kefumei/assets/ip-campaign.jpg') }}" alt="可复美 IP 联名活动" /><figcaption class="media-label">IP 联名</figcaption></figure>
            </div>
          </section>
        </div>
      </div>
    </section>

    <section class="band dark" id="retail">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">最后一公里，是门店能不能讲清楚。</h2>
          <p class="section-copy">材料中的门店陈列、O2O 上架、临床案例和常见问题，最终都要服务于店员开口推荐和消费者决策。</p>
        </div>
        <div class="system-panel">
          <div class="system-visual"><img src="{{ url_for('static', filename='projects/kefumei/assets/retail-display.jpg') }}" alt="可复美门店陈列" /></div>
          <div class="system-copy">
            <h3>陈列不是装饰，是增加被问起的机会。</h3>
            <p>门店内的收银台、橱窗和端架负责提高触达频率。对于高认知产品，清晰陈列能让店员推荐更自然。</p>
          </div>
          <div class="system-copy">
            <h3>O2O 和案例素材负责补齐决策信息。</h3>
            <p>线上头图承接搜索和即时购买，临床案例素材帮助店员解释使用场景，但页面不新增医学结论，只作为项目资料证据展示。</p>
          </div>
          <div class="system-visual"><img src="{{ url_for('static', filename='projects/kefumei/assets/o2o-channel.jpg') }}" alt="可复美 O2O 渠道头图" /></div>
          <div class="system-visual"><img src="{{ url_for('static', filename='projects/kefumei/assets/clinical-hand-case.jpg') }}" alt="可复美临床案例素材" /></div>
          <div class="system-copy">
            <h3>培训内容需要能被一线复述。</h3>
            <p>把复杂功效拆成“适合谁、为什么、怎么用、怎么和竞品区分”，才是真正能复制到门店和区域团队的项目资产。</p>
          </div>
        </div>
      </div>
    </section>

    <section class="band paper" id="outcome">
      <div class="section-inner">
        <div class="section-head">
          <h2 class="section-title">沉淀为四类可复用项目资产。</h2>
          <p class="section-copy">不虚构销售结果，只展示从材料中能归纳出的项目成果类型，后续可以继续补真实指标和复盘。</p>
        </div>
        <div class="outcome-grid">
          <article class="outcome-card"><h3>产品培训体系</h3><p>把重组胶原蛋白、医疗器械敷料、喷雾和修复乳组织成清晰的产品教育路径。</p></article>
          <article class="outcome-card"><h3>场景化推荐逻辑</h3><p>从敏感、痘痘、医美术后、日常修护等场景切入，帮助一线人员更容易解释产品。</p></article>
          <article class="outcome-card"><h3>内容传播证据</h3><p>沉淀明星达人、活动复盘、IP 联名和平台素材，支持品牌认知持续放大。</p></article>
          <article class="outcome-card"><h3>渠道动销承接</h3><p>把门店陈列、O2O 头图、常见问题和推荐动作整理为可复制的渠道执行素材。</p></article>
        </div>
      </div>
    </section>
  </main>

  <footer class="closing">
    <div class="closing-inner">
      <div>/me 路径下的私密项目案例 · me_session 仅限 /me 路径</div>
      <a class="back-link" href="/me/">返回个人首页</a>
    </div>
  </footer>

  <script>
    (() => {
      const root = document.documentElement;
      const nav = document.querySelector(".nav");
      const heroVisual = document.querySelector(".hero-visual");
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const updateScroll = () => {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const progress = Math.min(1, Math.max(0, window.scrollY / max));
        root.style.setProperty("--scroll", progress.toFixed(4));
        if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 12);
      };

      updateScroll();
      window.addEventListener("scroll", updateScroll, { passive: true });

      if (reduceMotion) return;
      root.classList.add("motion-ready");

      const revealItems = [
        ...document.querySelectorAll(".caption-item, .section-title, .section-copy, .work-card, .story, .media-tile, .system-visual, .system-copy, .outcome-card")
      ];

      revealItems.forEach((element, index) => {
        element.classList.add("reveal");
        element.style.setProperty("--delay", `${Math.min((index % 5) * 70, 280)}ms`);
      });

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });

      revealItems.forEach((element) => observer.observe(element));

      let raf = 0;
      const moveGlow = (event) => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          if (heroVisual) {
            const rect = heroVisual.getBoundingClientRect();
            const x = (event.clientX - rect.left) / rect.width - 0.5;
            const y = (event.clientY - rect.top) / rect.height - 0.5;
            const inside = x > -0.7 && x < 0.7 && y > -0.7 && y < 0.7;
            root.style.setProperty("--lift-x", inside ? `${x * 14}px` : "0px");
            root.style.setProperty("--lift-y", inside ? `${y * 10}px` : "0px");
            root.style.setProperty("--tilt-x", inside ? `${y * -3}deg` : "0deg");
            root.style.setProperty("--tilt-y", inside ? `${x * 4}deg` : "0deg");
          }

          document.querySelectorAll(".work-card, .outcome-card").forEach((card) => {
            const rect = card.getBoundingClientRect();
            const x = ((event.clientX - rect.left) / rect.width) * 100;
            const y = ((event.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty("--glow-x", `${x}%`);
            card.style.setProperty("--glow-y", `${y}%`);
          });
        });
      };

      window.addEventListener("pointermove", moveGlow, { passive: true });
      window.addEventListener("pointerleave", () => {
        root.style.setProperty("--lift-x", "0px");
        root.style.setProperty("--lift-y", "0px");
        root.style.setProperty("--tilt-x", "0deg");
        root.style.setProperty("--tilt-y", "0deg");
      });
    })();
  </script>
</body>
</html>
"""


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
