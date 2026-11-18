# 个人网站公开版 / 2026-11-17

由用户确认的 v7 私人预览整理，发布入口 `/profile`，资源入口 `/profile-assets/20261117-r1/`。保留完整公开 HTML、交互脚本、图片、可编辑 SVG 遮罩与许可证。没有包含 Obsidian 原始文档、内部事实核对数字、账号数据库、日志或凭证。

## 运行与编辑

在本目录 `npm install`，`npm run dev`；`npm run build` 产生版本化资源。正文直接编辑 `index.html`，布局在 `styles.css`，交互在 `app.js`，3D资料空间在 `space.js`。图片在 `assets/`，来源在 `ASSET-SOURCES.json`。SVG 是编辑源；执行 `npm run export:cutouts` 导出PNG后再构建。

私人预览记录与浏览器验收保留在本机 `previews/2026-11-17-product-market-v7/`。此公开目录不读取私人知识库。

## 部署

只替换公开 `/profile` 首页，旧项目页、私密 `/me/` 和其他业务由现有服务继续处理。部署脚本及回滚方法见 `deployment/profile-20261117-r1/`。不要用本地根目录旧 app.py 整站覆盖生产。
