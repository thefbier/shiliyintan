# -*- coding: utf-8 -*-
"""
generate_matrix.py — 十里银滩矩阵内容生成器
从站点数据 JSON（单一事实源）自动生成各平台成品稿包到 matrix_outbox/<日期>/。
用法:
    python scripts/generate_matrix.py              # 生成默认批次（3条小红书+2条抖音+1条头条+1份转发话术）
    python scripts/generate_matrix.py --limit 5    # 每类最多 N 条
    python scripts/generate_matrix.py --open       # 生成后列出文件
生成物为半自动 L2 级:AI 成品稿包,人工复制粘贴发布(约3分钟/篇),合规零封号风险。
"""
import argparse
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://shiliyintan.pages.dev"
CONTACT = "jinge@shiliyintan.cn"


def load(name):
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return None
    return json.load(io.open(path, encoding="utf-8"))


def write_out(subdir, fname, content):
    d = os.path.join(ROOT, "matrix_outbox", subdir)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fname)
    io.open(p, "w", encoding="utf-8").write(content)
    return p


# ---------- 小红书(FAQ→图文) ----------
def xiaohongshu_from_faq(f):
    title = f["q"]
    if len(title) > 20:
        title = title[:18] + "…"
    body = f["a"]
    tags = "#十里银滩 #惠州 #惠东 #过冬租房 #双月湾 #旅居 #海边生活"
    hook = "👆 收藏这篇,来了不踩坑。有问题评论区问我,每条都回。"
    guide = (
        "--- 发布信息 ---\n"
        "平台: 小红书\n"
        "建议配图(3张即可): 1)标题图(大字报:F01楼巴25元) 2)时刻表截图或站点FAQ页截图 3)海边封面图\n"
        "人工核对点: 车票价格/时刻为 2026-11-25 核查口径,发布时若超1个月请复查楼巴公众号\n"
        "建议发布时间: 周四-周五 18:00-21:00(通勤刷手机高峰)\n"
        "发布后动作: 简介挂独立站,评论区置顶\"完整清单看主页\"\n"
        "--- 正文开始 ---\n"
    )
    content = guide + f"\n【标题】{title}\n\n【正文】\n{body}\n\n{hook}\n\n【标签】{tags}\n"
    return content, title


# ---------- 抖音口播(每周一问→脚本) ----------
def douyin_from_round(r):
    q = r["question"]
    take = r.get("myTake", "")
    other = r.get("otherSide", "")
    handoff = r.get("handoff", "")
    script = (
        f"开头钩子(3秒): \"{q}\"\n\n"
        f"口播正文(约60秒): \n"
        f"我的判断是——{take}\n\n"
        f"但反方也不是没道理: {other}\n\n"
        f"结尾递话筒: {handoff} 评论区告诉我,每条必回。\n\n"
        f"画面提示: 站点FAQ页截图/海边空镜/楼巴站实拍素材(或用视频号文章转视频自动成片)\n"
    )
    t1 = q if len(q) <= 25 else q[:24] + "?"
    guide = (
        "--- 发布信息 ---\n"
        "平台: 抖音 / 快手(同稿改标题)\n"
        "备选标题: 1)" + t1 + "  2)住在十里银滩的人才知道的事  3)第一次见这么纠结的问题\n"
        "人工核对点: 数字口径以稿内标注为准;发布时勾选\"内容为AI辅助创作\"声明\n"
        "发布后动作: 置顶评论引导\"完整数据在主页链接\"\n"
        "--- 脚本开始 ---\n"
    )
    content = guide + f"\n{script}"
    return content, t1


# ---------- 头条/百家(FAQ汇总→SEO图文) ----------
def toutiao_from_faqs(faqs):
    title = "2026惠东十里银滩生活实录:楼巴、租房、就医、港人社区,一次说清"
    body_parts = []
    for f in faqs:
        body_parts.append(f"■ {f['q']}\n{f['a']}\n(信源:{f['source']} · 核查:{f['checkedOn']})\n")
    tail = f"完整清单持续更新于:{SITE} | 有补充或纠错可写信:{CONTACT} | 采用即署名。"
    guide = (
        "--- 发布信息 ---\n"
        "平台: 今日头条号 / 百家号(同稿双发)\n"
        "人工核对点: 各条数字为 2026-11-25/27 核查口径;发布时选择\"资讯-生活\"类目\n"
        "SEO关键词已内嵌: 十里银滩/惠东/楼巴/租房/过冬/港人\n"
        "--- 正文开始 ---\n"
    )
    content = guide + f"\n【标题】{title}\n\n" + "\n".join(body_parts) + f"\n{tail}\n"
    return content, title


# ---------- 转发话术(朋友圈/群) ----------
def share_scripts():
    lines = [
        "--- 朋友圈版(30字内) ---",
        "十里银滩的楼巴、租房、就医,一条条查清楚放在这了,含信源和核查日期。",
        "",
        "--- 街坊群版 ---",
        "整理了一份十里银滩生活清单(楼巴票价/租房行情/就医路径),每条都标了信源和核查日期,有错直接说,公开改。",
        f"完整版: {SITE}",
        "",
        "--- 针对候鸟群/港人群 ---",
        "准备来过冬/长住的可以看这个:楼巴怎么买票、租房真实行情、三甲医院多远,都是查证过的,不是中介文案。",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="矩阵内容稿包生成器")
    ap.add_argument("--limit", type=int, default=3, help="每类稿包上限")
    ap.add_argument("--open", action="store_true", help="生成后列出文件")
    args = ap.parse_args()

    faq = load("faq.json")
    host = load("host.json")
    if not faq or not host:
        sys.exit("缺少 faq.json / host.json")

    date = __import__("subprocess").run(
        ["git", "log", "-1", "--format=%ad", "--date=short"], cwd=ROOT,
        capture_output=True, text=True).stdout.strip() or "batch"
    made = []

    # 小红书: FAQ 每条一稿
    for f in faq.get("faqs", [])[: args.limit]:
        c, t = xiaohongshu_from_faq(f)
        made.append(write_out("xiaohongshu", f"{f['id']}.md", c))
    # 抖音: 最近擂台
    for r in host.get("rounds", [])[: max(1, args.limit - 1)]:
        c, t = douyin_from_round(r)
        made.append(write_out("douyin", f"{r['id']}.md", c))
    # 头条: FAQ 汇总
    c, t = toutiao_from_faqs(faq.get("faqs", [])[:6])
    made.append(write_out("toutiao", "faq-compilation.md", c))
    # 转发话术
    made.append(write_out(".", "share-scripts.md", share_scripts()))

    idx = ["# 本周矩阵稿包索引", "", "| 文件 | 平台 | 动作 |", "|---|---|---|"]
    for p in made:
        rel = os.path.relpath(p, os.path.join(ROOT, "matrix_outbox"))
        plat = rel.split(os.sep)[0] if os.sep in rel else "通用"
        idx.append(f"| {rel} | {plat} | 复制→粘贴→发布 |")
    idx_path = write_out(".", "_INDEX.md", "\n".join(idx) + "\n")

    print(f"[done] {len(made)} 个稿包 + 索引 -> {os.path.relpath(idx_path, ROOT)}")
    if args.open:
        for p in made:
            print("  ", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
