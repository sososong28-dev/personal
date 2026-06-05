# Profile Site

个人经历网站，作为独立 Flask 项目运行，当前线上挂载在 `/me`。

默认登录入口：

```text
http://<server-ip>/me/login
```

默认管理员账号：

```text
username: sososong
password: 由 PROFILE_ADMIN_PASSWORD 设置
```

> 注意：生产环境不要把真实密码提交到 GitHub。首次启动前必须在 `.env` 或 systemd 环境变量里设置 `PROFILE_ADMIN_PASSWORD`。

## 功能

- `/me/login`：登录页
- `/me/`：登录后的个人经历首页
- `/me/logout`：退出登录
- 独立 session cookie：`me_session`
- 独立 SQLite 数据库：`data/profile.db`
- 首次启动自动创建管理员账号
- 密码使用 Werkzeug 哈希保存，不以明文写入数据库

## 当前访问模式

当前按私密个人档案站运行：

- 除 `/me/login` 外，个人经历首页 `/me/` 必须登录后访问
- `me_session` cookie 的路径限制在 `/me`，避免发送到数据工具平台路径
- `/me` 相关响应会返回 `no-store` 和 `noindex` 头，减少浏览器缓存和搜索引擎索引风险
- 登录后首页可以放真实经历、项目资料、图片视频、简历文档和私密文章
- 如果未来需要公开展示页，建议新增独立公开路由，不要取消 `/me/` 的登录保护

## 项目结构

```text
profile-site/
├─ app.py                 # Flask 应用主文件
├─ wsgi.py                # Gunicorn / WSGI 入口
├─ gunicorn.conf.py       # Gunicorn 配置
├─ requirements.txt       # Python 依赖
├─ README.md              # 项目说明
├─ static/
│  └─ profile-archive-hero.png  # 首页和登录页视觉资产
├─ data/
│  └─ profile.db          # SQLite 数据库，首次启动自动创建
└─ logs/
   ├─ access.log
   └─ error.log
```

## 环境变量

可通过 `.env` 或 systemd `Environment=` 设置：

```text
PROFILE_ADMIN_USERNAME=sososong
PROFILE_ADMIN_PASSWORD=replace-with-initial-password
PROFILE_SECRET_KEY=change-to-a-random-secret
PORT=5001
```

说明：

- `PROFILE_ADMIN_USERNAME`：首次初始化管理员账号名。
- `PROFILE_ADMIN_PASSWORD`：首次初始化管理员密码。
- `PROFILE_SECRET_KEY`：Flask session 加密密钥，生产环境必须使用随机长字符串。
- `PORT`：仅用于直接 `python app.py` 启动；Gunicorn 使用 `gunicorn.conf.py`。

重要：管理员账号只在数据库不存在该用户名时自动创建。已经创建后，修改环境变量不会自动改数据库里的密码。

## 本地运行

```bash
cd profile-site
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PROFILE_SECRET_KEY="$(python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)" .venv/bin/python app.py
```

Windows PowerShell：

```powershell
cd profile-site
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:PROFILE_SECRET_KEY = [guid]::NewGuid().ToString("N")
.\.venv\Scripts\python app.py
```

本地访问：

```text
http://127.0.0.1:5001/me/login
```

## 服务器部署

推荐目录：

```text
/var/www/profile-site
```

部署步骤：

```bash
mkdir -p /var/www/profile-site
cd /var/www/profile-site
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p data logs
```

生产环境 `.env` 示例：

```bash
cat > /var/www/profile-site/.env <<'EOF'
PROFILE_SECRET_KEY=replace-with-random-secret
PROFILE_ADMIN_USERNAME=sososong
PROFILE_ADMIN_PASSWORD=replace-with-initial-password
EOF
chmod 600 /var/www/profile-site/.env
```

## Gunicorn

`gunicorn.conf.py` 当前配置：

```python
bind = "127.0.0.1:5001"
workers = 1
threads = 2
timeout = 60
accesslog = "logs/access.log"
errorlog = "logs/error.log"
```

手动启动：

```bash
cd /var/www/profile-site
.venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
```

## systemd

服务文件建议路径：

```text
/etc/systemd/system/profile-site.service
```

示例：

```ini
[Unit]
Description=Private profile site
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/profile-site
EnvironmentFile=-/var/www/profile-site/.env
ExecStart=/var/www/profile-site/.venv/bin/gunicorn -c /var/www/profile-site/gunicorn.conf.py wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：

```bash
systemctl daemon-reload
systemctl enable profile-site
systemctl restart profile-site
systemctl status profile-site
```

## Nginx

当前项目使用 `/me` 路径前缀。Nginx 不需要去掉 `/me`，直接转发即可：

```nginx
location = /me {
    return 301 /me/;
}

location /me/ {
    proxy_pass http://127.0.0.1:5001;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /me;
    proxy_read_timeout 3600;
    proxy_send_timeout 3600;
}
```

验证并重载：

```bash
nginx -t
systemctl reload nginx
```

## 登录与账号初始化

首次启动时，系统会创建管理员账号：

```text
sososong / <PROFILE_ADMIN_PASSWORD>
```

账号写入 SQLite 表：

```sql
users (
  id,
  username,
  password_hash,
  role,
  enabled,
  last_login_at,
  last_login_ip,
  created_at,
  updated_at
)
```

如果需要重置管理员密码，可用 Python 脚本更新：

```bash
cd /var/www/profile-site
.venv/bin/python - <<'PY'
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("data/profile.db")
conn.execute(
    "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
    (generate_password_hash("NewStrongPassword123!"), "sososong"),
)
conn.commit()
conn.close()
print("password updated")
PY
```

## 与数据网站共存

推荐共存方式：

```text
数据网站：   /data 或当前根路径
个人网站：   /me
```

两个站点应保持独立：

```text
数据站 cookie:     session 或 data_session
个人站 cookie:     me_session
数据站数据库:      /var/www/excel-tool/data/tools.db
个人站数据库:      /var/www/profile-site/data/profile.db
```

不要复用同一个数据库或同一个 session cookie 名称。

## 转移到新项目

迁移时复制这些文件即可：

```text
app.py
wsgi.py
gunicorn.conf.py
requirements.txt
README.md
static/
```

是否复制 `data/profile.db` 取决于目标：

- 要保留已有账号和登录记录：复制 `data/profile.db`
- 要重新初始化账号：不复制 `data/profile.db`，新环境首次启动会重新创建管理员

是否复制 `.env`：

- 同一服务器迁移：可以复制
- 新服务器或公开环境：建议重新生成 `PROFILE_SECRET_KEY`

## 安全建议

- 正式环境使用强密码，并只放在 `.env` 或服务器环境变量里
- 使用 HTTPS
- `PROFILE_SECRET_KEY` 必须是随机长字符串
- `.env` 权限建议 `600`
- 不要把 `.env`、`data/profile.db`、`logs/` 提交到公开仓库
- 如果未来开放访客账号，建议增加失败登录锁定和账号管理后台

## 当前线上状态

```text
服务名：profile-site
目录：/var/www/profile-site
端口：127.0.0.1:5001
入口：http://<server-ip>/me/login
管理员：sososong
```
