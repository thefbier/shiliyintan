# 十里银滩生活站 · 部署与自动更新手册

面向一人公司的零成本静态站：GitHub 存代码，Cloudflare Pages 托管与加速，
WorkBuddy 定时任务生成内容并自动上线，网站栏目随之更新。

**核查日期：2026-11-25。平台规则可能变化，执行前以各平台当日官方口径为准。**

---

## 0. 当前实际状态（2026-11-25）

| 项 | 状态 |
|---|---|
| GitHub 仓库 | `thefbier/shiliyintan`（公开，main 分支），代码已推送 |
| Cloudflare Pages | 项目 `shiliyintan` 已建，`https://shiliyintan.pages.dev` **已上线可访问** |
| 部署方式 | **Direct Upload（脚本直传）**，不依赖 GitHub App 授权 |
| 自定义域名 | `shiliyintan.cn` / `www` 已在 Pages 绑定，状态 `pending`（等 DNS 指向） |
| DNS / NS | 仍在新网（`ns11/ns12.xincache.com`），**未改动** |
| 企业邮箱 MX | `mxbiz1.qq.com` / `mxbiz2.qq.com` 两条完好，`jinge@shiliyintan.cn` 不受影响 |
| 自动更新链路 | 已实测跑通：新增内容 → git push → Direct Upload → 线上更新 |

**唯一待办**：去新网后台把 NS 改到 Cloudflare（见 §1.3），改完自定义域名会自动生效。

---

## 1. 目录结构

```
shiliyintan-site/
├── index.html              站点入口
├── assets/
│   ├── style.css           样式
│   └── app.js              渲染逻辑（读取 content.json）
├── content.json            唯一数据源：文章 / 商家 / 房源 / 站点信息
├── CNAME                   域名声明（GitHub 侧保留；CF 侧绑定走 API）
├── .gitignore
├── scripts/
│   ├── update_content.py   内容更新 + git push + 可选部署
│   └── deploy.py           Cloudflare Pages Direct Upload 部署
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

## 2. 部署架构（重要）

**用 Direct Upload，不用 GitHub App 自动构建。** 原因：Cloudflare 的 GitHub 授权在本机环境下会跳到需手动输入凭据的登录页，图形自动化不可靠；而 Direct Upload 用 API Token 直传，已在本机反复验证成功，且不依赖任何浏览器会话。

- **GitHub**：只作代码仓库，保存所有版本历史（满足"托管 GitHub"的意图）。
- **Cloudflare Pages**：托管与加速，证书自动签发。
- **Token 凭据**：默认读 `C:/Users/Administrator/.shiliyintan_cf_token`，
  不存在则回退 `C:/Users/Administrator/.dressodm_cf_token`（同一账号的永久 Token，Pages 编辑权限）。
  删除这两个文件即停用自动部署（明确报 `NEED_TOKEN`，不硬失败）。
- **运行环境**：部署脚本依赖 `blake3`，用 `D:/Python314/python.exe` 运行；
  `update_content.py` 会自动回退到该解释器，定时任务无需关心。

手动重新部署：

```bash
cd shiliyintan-site
"D:/Python314/python.exe" scripts/deploy.py
```

---

## 3. DNS / NS 迁移清单（唯一待你操作的一步）

> 目标：把 `shiliyintan.cn` 的权威 DNS 从新网迁到 Cloudflare，让已绑定的自定义域名生效。
> **红线：企业邮箱 MX 记录必须原样保留，否则 `jinge@shiliyintan.cn` 会失效。**

### 3.1 在 Cloudflare 侧（可用网页操作，或用已登录的浏览器）

1. 登录 Cloudflare → **Add a site** → 输入 `shiliyintan.cn` → Free 计划 → 扫描现有 DNS 记录。
2. 扫描完成后，**核对并保留**以下记录（Cloudflare 通常会自动导入）：
   - `MX`  `@`  → `mxbiz1.qq.com`（优先级 5）
   - `MX`  `@`  → `mxbiz2.qq.com`（优先级 10）
   
   若 Cloudflare 没有自动导入，**手动补上这两条**，否则企业邮箱会失效。
3. Cloudflare 会分配两个 nameserver（形如 `xxx.ns.cloudflare.com`），记下来。
4. SSL/TLS → Overview → 加密模式选 **Full (Strict)**；Edge Certificates 确认 Universal SSL 签发；开启 **Always Use HTTPS**。
5. Pages 项目 → `shiliyintan` → Custom domains，确认 `shiliyintan.cn` 和 `www.shiliyintan.cn` 都在（已由 API 绑定，迁移 NS 后会自动从 `pending` 转为 `active`）。

### 3.2 在新网侧（注册商后台，需你本人登录操作）

1. 登录新网（xinnet.com）或用企业微信后台的域名管理入口，找到 `shiliyintan.cn`。
2. 把 NS 改为 Cloudflare 在 3.1 第 3 步给出的两个 nameserver。
3. 保存，等待生效（通常几分钟到数小时）。

> 顺序理由：先在 Cloudflare 侧配好站点、DNS 与证书，再切 NS，避免切换期间解析中断。
> 本会话**不会**替你改注册商设置，以免误伤企业邮箱。

### 3.3 切换后验证

```bash
nslookup -type=NS shiliyintan.cn      # 应显示 *.ns.cloudflare.com
nslookup -type=MX shiliyintan.cn      # 应仍显示 mxbiz1/mxbiz2.qq.com
```

打开 `https://shiliyintan.cn`，应显示站点且 HTTPS 锁标正常；
`jinge@shiliyintan.cn` 仍应能收信。

---

## 4. 验证清单

- [x] `https://shiliyintan.pages.dev` 能打开（部署成功）
- [x] 首页四个高频入口、数据条、文章、商家、房源均正常显示
- [x] 手机端菜单能展开/收起
- [x] 修改 `content.json` 并运行更新脚本后，线上内容立即更新（Direct Upload）
- [ ] `https://shiliyintan.cn` 能打开且显示 HTTPS 锁标（待 NS 迁移）
- [ ] NS 迁移后 `jinge@shiliyintan.cn` 仍能收信（MX 未被误删）

---

## 5. 自动更新：WorkBuddy 定时任务

### 5.1 原理

定时任务每次运行：生成内容 → 调用脚本写入 `content.json` → 脚本自动 `git push` 留存代码 +
`Direct Upload` 部署 → 线上栏目立即更新。全程无需浏览器、无需 GitHub 授权。

### 5.2 定时任务 Prompt 模板

工作目录设为 `F:/WorkBuddy/2026-11-24-01-32-05/shiliyintan-site`，Prompt 用下面这段：

```
任务：为十里银滩生活站生成今日内容并发布。

背景：面向候鸟、港人、长住业主的本地生活信息站，数据全部在 content.json。
选题围绕：租房避坑、真实生活成本、楼巴交通、就医教育、盐雾防腐、本地商家、社群活动。
所有事实性内容必须联网核查当日口径，标注来源与日期；不承诺升值、不渲染崩盘、不编造商家信息。

执行步骤：
1. 联网核查 1 个当日相关的本地信息点（交通/天气/政策/社区动态等），确认来源可靠。
2. 把文章写成临时文件 payload.json（放站点目录下），格式：
   {"title":"标题","category":"分类","excerpt":"摘要","tags":["标签1","标签2"],
    "sections":[{"heading":"小标题","text":"正文"},{"heading":"小标题2","text":"正文2"}]}
3. 执行一条命令完成入库+推送+上线：
   "D:/Python314/python.exe" scripts/update_content.py add-post --json payload.json --push --deploy
4. 如当日发现可核实的商家或房源信息，用 add-business / add-listing 命令追加（同样带 --push --deploy）。
5. 删除临时文件 payload.json。
6. 在输出中报告：新增了什么、git push 是否成功、线上部署 ID、预计生效时间。

约束：
- 不要修改 index.html / assets/ 下的文件。
- 不要删除 content.json 中已有的任何条目。
- 每条内容日期用当日北京时间。
- 若 git push 或部署失败，明确报告错误，不要静默跳过。
- 部署依赖 C:/Users/Administrator/.dressodm_cf_token（或 .shiliyintan_cf_token），不要读取或显示 token 内容。
```

### 5.3 建议频率

| 内容 | 频率 | 理由 |
|---|---|---|
| 落地指南文章 | 每天 1 篇 | 内容站靠持续更新建立搜索权重 |
| 商家/房源信息 | 每周 2–3 条 | 依赖真实信息源，不宜机械灌水 |
| 站点更新日期 | 每次更新自动同步 | 脚本已自动写入 |

---

## 6. 合规与风险

1. 域名为 `.cn`，托管在境外且面向大陆访客，严格口径下经营性网站需 ICP 备案，境外托管无法备案。
   建议先以**非经营性信息站**运行；若后续接入收费、交易，需评估备案与主体方案。
2. 本站不代收押金、租金或任何资金；房源与商家信息仅作展示，交易双方自行交割。
3. 房价、入住率等敏感数据标注来源与日期，不承诺升值、不渲染崩盘。
4. 用户提供的企业邮箱初始密码属敏感信息，不在本站任何文件中保存；激活后应立即修改。
5. `shiliyintan.com` 归属不明，本项目不使用；唯一域名为 `shiliyintan.cn`。

---

## 7. 常见问题

**Q：为什么不用 GitHub Pages + Cloudflare 橙云代理？**
A：2026 年该组合存在已知的 SSL 证书签发冲突（`NotServedByPagesError`），
Cloudflare 代理 IP 会干扰 GitHub 的 Let's Encrypt 验证。Cloudflare Pages 让 DNS 与托管同处一家，
证书自动签发，且国内访问速度在免费方案中较优，因此选它。GitHub 仍作为代码仓库，满足你的意图。

**Q：为什么不用 Cloudflare 的 GitHub 自动构建？**
A：GitHub 授权页在本机图形环境下需手动输入凭据，不稳定；Direct Upload 用 API Token 直传，
已实测可靠，且定时任务可一条命令完成。代码仍完整保存在 GitHub。

**Q：内容更新后多久能看到？**
A：`--deploy` 执行完即已上线（约几十秒）；浏览器可能有缓存，强刷即可。

**Q：误删了内容怎么办？**
A：所有内容都在 git 里，用 `git log` 找到上一次提交，`git revert` 即可回滚后重新部署。
