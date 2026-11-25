# 十里银滩生活站 · 部署与自动更新手册

面向一人公司的零成本静态站：GitHub 存代码，Cloudflare Pages 托管与加速，
WorkBuddy 定时任务生成内容并自动推送，网站栏目随之更新。

**核查日期：2026-11-24/25。平台规则可能变化，执行前以各平台当日官方口径为准。**

---

## 0. 目录结构

```
shiliyintan-site/
├── index.html              站点入口
├── assets/
│   ├── style.css           样式
│   └── app.js              渲染逻辑（读取 content.json）
├── content.json            唯一数据源：文章 / 商家 / 房源 / 站点信息
├── CNAME                   自定义域名声明
├── scripts/
│   └── update_content.py   内容更新 + git push 工具
└── README.md               本文件
```

本地预览：

```bash
cd shiliyintan-site
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

不要直接双击 index.html：浏览器会阻止 `file://` 下的 JSON 读取。

---

## 1. 一次性部署清单（约 30–60 分钟）

### 1.1 GitHub 仓库

1. 登录 GitHub，账号 `thefbier`，新建仓库，建议名 `shiliyintan`。
2. 设为 **Public**（Cloudflare Pages 免费版读取公开仓库最省事；私有仓库需授权）。
3. 不要勾选 README / .gitignore（保持空仓库，便于首次推送）。
4. 本地初始化并推送：

```bash
cd shiliyintan-site
git init
git add .
git commit -m "init: 十里银滩生活站"
git branch -M main
git remote add origin https://github.com/thefbier/shiliyintan.git
git push -u origin main
```

> 若本机 `git push` 遇 TLS/代理问题，可改用 Personal Access Token 作为密码，
> 或使用 GitHub Desktop。推送这一步只需成功一次。

### 1.2 Cloudflare Pages 连接仓库

1. 登录 Cloudflare → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**。
2. 选择 GitHub → 授权 → 选中 `thefbier/shiliyintan`。
3. 构建配置（本站点是纯静态，无需构建）：

| 项 | 值 |
|---|---|
| Production branch | `main` |
| Build command | 留空 |
| Build output directory | `/`（根目录） |

4. 首次部署完成后，Cloudflare 会分配临时域名 `https://shiliyintan.pages.dev`，用它先验证站点。

### 1.3 DNS 与 NS 迁移（关键，顺序不能乱）

本站点**不使用 GitHub Pages 的 SSL 证书机制**，因此不需要"灰云签证书再切橙云"的规避流程——
证书由 Cloudflare 在边缘自动签发。这是选 Cloudflare Pages 而非 GitHub Pages 的主要原因。

1. 在 Cloudflare 添加站点 `shiliyintan.cn`（Free 计划即可），它会扫描现有记录。
2. 确认有以下记录（Cloudflare Pages 绑定域名时会自动添加，或手动加）：
   - 类型 `CNAME`，名称 `@`（或根域），目标 `shiliyintan.pages.dev`（或 Pages 给出的 CNAME 目标）。
   - 类型 `CNAME`，名称 `www`，目标同上。
   - 保留腾讯企业邮箱的 MX 记录（`mxbiz1.qq.com` / `mxbiz2.qq.com`），**不要删除**，否则邮箱会失效。
3. SSL/TLS → Overview → 加密模式选 **Full (Strict)**；
   Edge Certificates 里确认 Universal SSL 已签发，开启 **Always Use HTTPS**。
4. 最后一步才去新网后台把 NS 改为 Cloudflare 分配的两个 nameserver：

```
（Cloudflare 会给出具体值，形如 xxx.ns.cloudflare.com）
```

> 顺序理由：先在 Cloudflare 侧配好站点与证书，再切 NS，可避免切换期间解析中断。
> NS 变更全球生效通常需要数分钟到数小时。切换前建议把 TTL 降到 600。

### 1.4 自定义域名绑定到 Pages

在 Cloudflare Pages 项目 → **Custom domains** → **Set up a custom domain** →
输入 `shiliyintan.cn` → 按提示添加/确认 DNS 记录 → 等待证书签发（通常几分钟）。

完成后访问 `https://shiliyintan.cn` 应显示站点。

---

## 2. 验证清单

- [ ] `https://shiliyintan.pages.dev` 能打开（部署成功）
- [ ] `https://shiliyintan.cn` 能打开且显示 HTTPS 锁标（证书成功）
- [ ] 首页四个高频入口、数据条、文章、商家、房源均正常显示
- [ ] 手机端菜单能展开/收起
- [ ] `jinge@shiliyintan.cn` 企业邮箱仍能收信（MX 未被误删）
- [ ] 修改 `content.json` 并 push 后，约 1–2 分钟内线上内容更新

---

## 3. 自动更新：WorkBuddy 定时任务

### 3.1 原理

定时任务每次运行做三件事：生成内容 → 调用脚本写入 `content.json` → 脚本自动 `git push` →
Cloudflare Pages 检测到新提交后重新构建 → 线上栏目更新。全程无需人工操作。

### 3.2 定时任务 Prompt 模板

在创建定时任务时，工作目录设为 `F:/WorkBuddy/2026-11-24-01-32-05/shiliyintan-site`，
Prompt 可直接用下面这段（方括号处按当日实际情况填写）：

```
任务：为十里银滩生活站生成今日内容并发布。

背景：站点是面向候鸟、港人、长住业主的本地生活信息站，数据全部存放在 content.json。
文章选题围绕：租房避坑、真实生活成本、楼巴交通、就医教育、盐雾防腐、本地商家、社群活动。
所有事实性内容必须联网核查当日口径，标注来源与日期；不承诺升值、不渲染崩盘、不编造商家信息。

执行步骤：
1. 联网核查 1 个当日相关的本地信息点（交通/天气/政策/社区动态等），确认来源可靠。
2. 用以下脚本新增 1 篇文章（把内容写成 JSON 文件后调用，避免命令行转义问题）：
   先把文章写入临时文件 payload.json，格式：
   {"title":"标题","category":"分类","excerpt":"摘要","tags":["标签1","标签2"],
    "sections":[{"heading":"小标题","text":"正文"},{"heading":"小标题2","text":"正文2"}]}
   然后执行：python scripts/update_content.py add-post --json payload.json --push
3. 如当日发现可核实的商家或房源信息，用对应的 add-business / add-listing 命令追加（同样带 --push）。
4. 在输出中报告：新增了什么、推送是否成功、线上预计更新时间。

约束：
- 不要修改 index.html / assets/ 下的文件。
- 不要删除 content.json 中已有的任何条目。
- 每条内容日期用当日北京时间。
- 若 git push 失败，明确报告错误，不要静默跳过。
```

### 3.3 建议频率

| 内容 | 频率 | 理由 |
|---|---|---|
| 落地指南文章 | 每天 1 篇 | 内容站靠持续更新建立搜索权重 |
| 商家/房源信息 | 每周 2–3 条 | 依赖真实信息源，不宜机械灌水 |
| 站点更新日期 | 每次更新自动同步 | 脚本已自动写入 |

先用"每天 1 篇"跑两周，观察搜索引擎收录与访问数据，再决定是否加频。

### 3.4 本机环境提醒

- Cloudflare 控制台在国内直连可能卡加载，必要时先开 v2rayN 并启用 Tun。
- 本机 `git push` 到 GitHub 若报 TLS 错误，可用 `--ssl-no-revoke`（curl 场景）或改用 Token/Desktop。
- 若 wrangler 部署超时，Cloudflare Pages 已通过 Git 自动构建，无需 wrangler 介入。

---

## 4. 合规与风险

1. 域名为 `.cn`，托管在境外且面向大陆访客，严格口径下经营性网站需 ICP 备案，境外托管无法备案。
   建议先以**非经营性信息站**运行；若后续接入收费、交易，需评估备案与主体方案。
2. 本站不代收押金、租金或任何资金；房源与商家信息仅作展示，交易双方自行交割。
3. 房价、入住率等敏感数据标注来源与日期，不承诺升值、不渲染崩盘。
4. 用户提供的企业邮箱初始密码属敏感信息，不在本站任何文件中保存；激活后应立即修改。
5. `shiliyintan.com` 归属不明，本项目不使用；唯一域名为 `shiliyintan.cn`。

---

## 5. 常见问题

**Q：为什么不用 GitHub Pages + Cloudflare 橙云代理？**
A：2026 年该组合存在已知的 SSL 证书签发冲突（`NotServedByPagesError`），
Cloudflare 代理 IP 会干扰 GitHub 的 Let's Encrypt 验证。Cloudflare Pages 让 DNS 与托管同处一家，
证书自动签发，且国内访问速度在免费方案中较优，因此选它。GitHub 仍作为代码仓库，满足你的意图。

**Q：内容更新后多久能看到？**
A：push 后 Cloudflare Pages 通常 1–2 分钟完成构建；浏览器可能有缓存，强刷即可。

**Q：误删了内容怎么办？**
A：所有内容都在 git 里，用 `git log` 找到上一次提交，`git revert` 即可回滚。
