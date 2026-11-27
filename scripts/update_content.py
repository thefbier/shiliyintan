#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""十里银滩生活站 · 内容更新与推送工具

供 WorkBuddy 定时任务调用：把生成的内容写入对应数据文件，并可选自动 git commit/push
与 Cloudflare Pages 部署。全部使用标准库。

数据文件：
  content.json     落地指南文章 / 商家 / 房源 / 站点信息
  host.json        开台白 / 每周擂台 / 回声墙 / 站规
  community.json   关系交换机 / 立场专栏 / 社区活动

用法示例：
  # 落地指南
  python scripts/update_content.py add-post --json payload.json --push --deploy
  # 每周擂台（自动供稿主力）
  python scripts/update_content.py add-round --json round.json --push --deploy
  # 回声（读者接话，需本人认领）
  python scripts/update_content.py add-echo --json echo.json --push --deploy
  # 立场专栏
  python scripts/update_content.py add-column --json column.json --push --deploy
  # 兼容旧命令
  python scripts/update_content.py add-business --name "店名" --area "五期" --desc "描述"
  python scripts/update_content.py add-listing --title "房源" --price "600元/月"
  python scripts/update_content.py set-site --updated 2026-11-27 --notice "公告"

  任意命令加 --push 提交推送；加 --deploy 部署到 Cloudflare Pages；
  加 --dry-run 只打印将执行的操作。--push/--deploy 可写在命令任意位置。
"""

import argparse
import datetime as dt
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_PATH = os.path.join(ROOT, 'content.json')
HOST_PATH = os.path.join(ROOT, 'host.json')
COMMUNITY_PATH = os.path.join(ROOT, 'community.json')

FILE_FOR_CMD = {
    'add-post': 'content.json',
    'add-business': 'content.json',
    'add-listing': 'content.json',
    'set-site': 'content.json',
    'add-round': 'host.json',
    'add-echo': 'host.json',
    'add-column': 'community.json',
}
TRACKED_FILES = ['content.json', 'host.json', 'community.json', 'businesses.json', 'sources.json',
                 'index.html', 'assets/app.js', 'assets/style.css']


def path_of(name):
    return {'content.json': CONTENT_PATH, 'host.json': HOST_PATH,
            'community.json': COMMUNITY_PATH}.get(name, os.path.join(ROOT, name))


def load_json(name):
    with io.open(path_of(name), 'r', encoding='utf-8') as f:
        return json.load(f)


def load_content():
    return load_json('content.json')


def save_json(name, data, dry_run=False):
    if dry_run:
        print('[dry-run] 跳过写入 ' + name)
        return
    with io.open(path_of(name), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('[ok] 已写入 ' + name)


def save_content(data, dry_run=False):
    save_json('content.json', data, dry_run)


def next_id(prefix, items):
    nums = []
    for it in items:
        raw = str(it.get('id', ''))
        if raw.startswith(prefix) and raw[len(prefix):].isdigit():
            nums.append(int(raw[len(prefix):]))
    return '{}{:03d}'.format(prefix, max(nums) + 1 if nums else 1)


def parse_sections(text):
    """格式：小标题|正文;;小标题2|正文2"""
    result = []
    if not text:
        return result
    for chunk in text.split(';;'):
        if '|' not in chunk:
            continue
        heading, body = chunk.split('|', 1)
        if heading.strip() or body.strip():
            result.append({'h': heading.strip(), 'p': body.strip()})
    return result


def parse_post_sections(text):
    result = parse_sections(text)
    return [{'heading': x['h'], 'text': x['p']} for x in result]


def parse_tags(text):
    if not text:
        return []
    if isinstance(text, list):
        return text
    return [t.strip() for t in text.replace('，', ',').split(',') if t.strip()]


def read_json_arg(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def today():
    return dt.date.today().isoformat()


def collect_payload(args):
    """从 --json 文件或命令行参数收集字段。"""
    if getattr(args, 'json', None):
        return read_json_arg(args.json)
    keys = ('title', 'category', 'date', 'excerpt', 'tags', 'sections',
            'name', 'area', 'desc', 'contact', 'type', 'price', 'note',
            'updated', 'notice', 'domain', 'tagline', 'description',
            'week', 'kicker', 'question', 'myTake', 'otherSide', 'whyAsk',
            'handoff', 'status', 'stand', 'read', 'cta', 'voice', 'to', 'from_')
    payload = {}
    for key in keys:
        value = getattr(args, key, None)
        if value is not None:
            payload[key] = value
    return payload


# ---------------- content.json ----------------
def cmd_add_post(data, args):
    p = collect_payload(args)
    posts = data.setdefault('posts', [])
    secs = p.get('sections')
    if isinstance(secs, str):
        secs = parse_post_sections(secs)
    item = {
        'id': p.get('id') or next_id('p', posts),
        'title': p.get('title', '未命名文章'),
        'category': p.get('category', '指南'),
        'date': p.get('date') or today(),
        'tags': parse_tags(p.get('tags')),
        'excerpt': p.get('excerpt', ''),
        'sections': secs or []
    }
    posts.insert(0, item)
    data.setdefault('site', {})['updated'] = item['date']
    print('[ok] 新增文章：{} ({})'.format(item['title'], item['id']))
    return 'add post: ' + item['title']


def cmd_add_business(data, args):
    p = collect_payload(args)
    items = data.setdefault('businesses', [])
    item = {
        'id': p.get('id') or next_id('b', items),
        'name': p.get('name', '未命名商家'),
        'category': p.get('category', '生活服务'),
        'area': p.get('area', ''),
        'desc': p.get('desc', ''),
        'contact': p.get('contact', '到店咨询'),
        'tags': parse_tags(p.get('tags'))
    }
    items.insert(0, item)
    data.setdefault('site', {})['updated'] = today()
    print('[ok] 新增商家：{} ({})'.format(item['name'], item['id']))
    return 'add business: ' + item['name']


def cmd_add_listing(data, args):
    p = collect_payload(args)
    items = data.setdefault('listings', [])
    item = {
        'id': p.get('id') or next_id('l', items),
        'title': p.get('title', '未命名房源'),
        'type': p.get('type', '整租'),
        'area': p.get('area', ''),
        'price': p.get('price', '价格面议'),
        'date': p.get('date') or today(),
        'note': p.get('note', '价格与条款以房东当日口径为准。')
    }
    items.insert(0, item)
    data.setdefault('site', {})['updated'] = item['date']
    print('[ok] 新增房源：{} ({})'.format(item['title'], item['id']))
    return 'add listing: ' + item['title']


def cmd_set_site(data, args):
    p = collect_payload(args)
    site = data.setdefault('site', {})
    changed = []
    for key in ('updated', 'notice', 'domain', 'tagline', 'description', 'name'):
        if key in p:
            site[key] = p[key]
            changed.append(key)
    print('[ok] 更新站点信息：{}'.format(', '.join(changed) if changed else '无变更'))
    return 'update site info'


# ---------------- host.json ----------------
def cmd_add_round(data, args):
    p = collect_payload(args)
    rounds = data.setdefault('rounds', [])
    item = {
        'id': p.get('id') or next_id('D', rounds),
        'week': p.get('week', ''),
        'kicker': p.get('kicker', '本周擂台'),
        'question': p.get('question', '未命名议题'),
        'myTake': p.get('myTake', ''),
        'otherSide': p.get('otherSide', ''),
        'whyAsk': p.get('whyAsk', ''),
        'handoff': p.get('handoff', ''),
        'status': p.get('status', '进行中 · 等你接')
    }
    # 反自嗨硬约束：立场、反方、递话筒三者缺一不可
    for k in ('myTake', 'otherSide', 'handoff'):
        if not item[k]:
            print('[warn] 擂台缺少 ' + k + '（反自嗨硬约束要求三者齐全）', file=sys.stderr)
    rounds.insert(0, item)
    max_rounds = int(getattr(args, 'max_rounds', 6) or 6)
    if len(rounds) > max_rounds:
        del rounds[max_rounds:]
    print('[ok] 新增擂台：{} ({})'.format(item['question'], item['id']))
    return 'add round: ' + item['question']


def cmd_add_echo(data, args):
    p = collect_payload(args)
    echoes = data.setdefault('echoes', [])
    item = {
        'id': p.get('id') or next_id('E', echoes),
        'to': p.get('to', ''),
        'from': p.get('from_') or p.get('from') or '待认领',
        'voice': p.get('voice', ''),
        'status': p.get('status', '示例 · 待本人认领')
    }
    echoes.insert(0, item)
    max_echoes = int(getattr(args, 'max_echoes', 12) or 12)
    if len(echoes) > max_echoes:
        del echoes[max_echoes:]
    print('[ok] 新增回声：{} ({})'.format(item['from'], item['id']))
    return 'add echo: ' + item['id']


# ---------------- community.json ----------------
def cmd_add_column(data, args):
    p = collect_payload(args)
    cols = data.setdefault('columns', [])
    secs = p.get('sections')
    if isinstance(secs, str):
        secs = parse_sections(secs)
    item = {
        'id': p.get('id') or next_id('V', cols),
        'title': p.get('title', '未命名专栏'),
        'kicker': p.get('kicker', '立场'),
        'date': p.get('date') or today(),
        'read': p.get('read', '5分钟'),
        'stand': p.get('stand', ''),
        'sections': secs or [],
        'cta': p.get('cta', '你怎么看？在关系交换机里接这句话。')
    }
    cols.insert(0, item)
    max_cols = int(getattr(args, 'max_columns', 10) or 10)
    if len(cols) > max_cols:
        del cols[max_cols:]
    print('[ok] 新增立场专栏：{} ({})'.format(item['title'], item['id']))
    return 'add column: ' + item['title']


HANDLERS = {
    'add-post': cmd_add_post, 'add-business': cmd_add_business,
    'add-listing': cmd_add_listing, 'set-site': cmd_set_site,
    'add-round': cmd_add_round, 'add-echo': cmd_add_echo,
    'add-column': cmd_add_column,
}


# ---------------- 推送 / 部署 ----------------
def git_push(message, dry_run=False):
    if dry_run:
        print('[dry-run] 跳过 git commit/push')
        return
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full = '[auto] {} · {}'.format(message, stamp)
    try:
        add_files = [f for f in TRACKED_FILES if os.path.isfile(os.path.join(ROOT, f))]
        subprocess.check_call(['git', 'add', '--'] + add_files, cwd=ROOT)
        result = subprocess.call(['git', 'commit', '-m', full], cwd=ROOT)
        if result == 0:
            subprocess.check_call(['git', 'push', 'origin', 'HEAD:main'], cwd=ROOT)
            print('[ok] 已提交并推送：' + full)
        else:
            print('[info] 无内容变更，跳过提交')
    except subprocess.CalledProcessError as e:
        print('[error] git 操作失败：{}'.format(e), file=sys.stderr)
        print('[hint] 确认已 git init、已配置 remote，且有推送权限。', file=sys.stderr)
        sys.exit(2)


def cloudflare_deploy(dry_run=False):
    if dry_run:
        print('[dry-run] 跳过 Cloudflare 部署')
        return
    deploy_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deploy.py')
    py = sys.executable
    try:
        import blake3  # noqa: F401
    except ImportError:
        fallback = r'D:/Python314/python.exe'
        if os.path.isfile(fallback):
            py = fallback
        else:
            print('[error] 缺少 blake3 且找不到 D:/Python314/python.exe，无法部署', file=sys.stderr)
            sys.exit(3)
    try:
        subprocess.check_call([py, deploy_py], cwd=ROOT)
        print('[ok] Cloudflare Pages 部署完成')
    except subprocess.CalledProcessError as e:
        print('[error] 部署失败：{}'.format(e), file=sys.stderr)
        sys.exit(4)


def build_parser():
    parser = argparse.ArgumentParser(description='十里银滩生活站内容更新工具')
    parser.add_argument('--push', action='store_true', help='写入后自动 git commit/push')
    parser.add_argument('--deploy', action='store_true', help='写入后自动部署到 Cloudflare Pages')
    parser.add_argument('--dry-run', action='store_true', help='只打印操作，不写入不推送')
    sub = parser.add_subparsers(dest='command')

    def common(sp):
        sp.add_argument('--json', help='从 JSON 文件读取全部字段（推荐供 AI 调用）')
        sp.add_argument('--push', action='store_true')
        sp.add_argument('--deploy', action='store_true')
        sp.add_argument('--dry-run', action='store_true')

    sp = sub.add_parser('add-post', help='新增落地指南')
    common(sp)
    for k in ('title', 'category', 'date', 'excerpt', 'tags', 'sections', 'id'):
        sp.add_argument('--' + k)

    sp = sub.add_parser('add-business', help='新增商家')
    common(sp)
    for k in ('name', 'category', 'area', 'desc', 'contact', 'tags', 'id'):
        sp.add_argument('--' + k)

    sp = sub.add_parser('add-listing', help='新增房源')
    common(sp)
    for k in ('title', 'type', 'area', 'price', 'date', 'note', 'id'):
        sp.add_argument('--' + k)

    sp = sub.add_parser('set-site', help='更新站点信息')
    common(sp)
    for k in ('updated', 'notice', 'domain', 'tagline', 'description', 'name'):
        sp.add_argument('--' + k)

    sp = sub.add_parser('add-round', help='新增每周擂台（自动供稿主力）')
    common(sp)
    for k in ('id', 'week', 'kicker', 'question', 'myTake', 'otherSide', 'whyAsk', 'handoff', 'status'):
        sp.add_argument('--' + k)
    sp.add_argument('--max-rounds', type=int, default=6, help='最多保留擂台数，默认6')

    sp = sub.add_parser('add-echo', help='新增回声（需本人认领）')
    common(sp)
    for k in ('id', 'to', 'voice', 'status'):
        sp.add_argument('--' + k)
    sp.add_argument('--from', dest='from_', help='发言者（须本人认领或授权）')
    sp.add_argument('--max-echoes', type=int, default=12, help='最多保留回声数，默认12')

    sp = sub.add_parser('add-column', help='新增立场专栏')
    common(sp)
    for k in ('id', 'title', 'kicker', 'date', 'read', 'stand', 'sections', 'cta'):
        sp.add_argument('--' + k)
    sp.add_argument('--max-columns', type=int, default=10, help='最多保留专栏数，默认10')

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    fname = FILE_FOR_CMD[args.command]
    data = load_json(fname)
    message = HANDLERS[args.command](data, args)
    save_json(fname, data, dry_run=args.dry_run)
    if getattr(args, 'push', False):
        git_push(message, dry_run=args.dry_run)
    if getattr(args, 'deploy', False):
        cloudflare_deploy(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
