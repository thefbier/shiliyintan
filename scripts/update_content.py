#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""十里银滩生活站 · 内容更新与推送工具

供 WorkBuddy 定时任务调用：把生成的内容写入 content.json，并可选自动 git commit/push。

用法示例：
  python scripts/update_content.py add-post --title "标题" --category "交通" \
      --date 2026-11-25 --excerpt "摘要" --tags "交通,楼巴" \
      --sections "小标题|正文;;小标题2|正文2"

  python scripts/update_content.py add-post --json payload.json
  python scripts/update_content.py add-business --name "店名" --category "维修" --area "五期" --desc "描述" --contact "电话"
  python scripts/update_content.py add-listing --title "房源" --type "长租" --area "三期" --price "600元/月" --note "备注"
  python scripts/update_content.py set-site --updated 2026-11-25 --notice "公告文字"

  以上任意命令加 --push 会在写入后自动提交并推送到远程仓库。
  加 --dry-run 只打印将要执行的操作，不写入、不推送。

注意：脚本使用标准库，不依赖第三方包。提交信息带时间戳，便于定时任务追溯。
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


def load_content():
    with io.open(CONTENT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_content(data, dry_run=False):
    if dry_run:
        print('[dry-run] 跳过写入 content.json')
        return
    with io.open(CONTENT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('[ok] 已写入 content.json')


def next_id(prefix, items):
    nums = []
    for it in items:
        raw = str(it.get('id', ''))
        if raw.startswith(prefix) and raw[len(prefix):].isdigit():
            nums.append(int(raw[len(prefix):]))
    return '{}{:03d}'.format(prefix, max(nums) + 1 if nums else 1)


def parse_sections(text):
    """格式：标题|正文;;标题2|正文2"""
    result = []
    if not text:
        return result
    for chunk in text.split(';;'):
        if '|' not in chunk:
            continue
        heading, body = chunk.split('|', 1)
        if heading.strip() or body.strip():
            result.append({'heading': heading.strip(), 'text': body.strip()})
    return result


def parse_tags(text):
    if not text:
        return []
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
    payload = {}
    for key in ('title', 'category', 'date', 'excerpt', 'tags', 'sections',
                'name', 'area', 'desc', 'contact', 'type', 'price', 'note',
                'updated', 'notice', 'domain', 'tagline', 'description'):
        value = getattr(args, key, None)
        if value is not None:
            payload[key] = value
    return payload


def cmd_add_post(data, args):
    p = collect_payload(args)
    posts = data.setdefault('posts', [])
    item = {
        'id': p.get('id') or next_id('p', posts),
        'title': p.get('title', '未命名文章'),
        'category': p.get('category', '指南'),
        'date': p.get('date') or today(),
        'tags': parse_tags(p.get('tags')) if isinstance(p.get('tags'), str) else (p.get('tags') or []),
        'excerpt': p.get('excerpt', ''),
        'sections': p.get('sections') if isinstance(p.get('sections'), list) else parse_sections(p.get('sections'))
    }
    posts.insert(0, item)
    # 同步站点更新日期
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
        'tags': parse_tags(p.get('tags')) if isinstance(p.get('tags'), str) else (p.get('tags') or [])
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


def git_push(message, dry_run=False):
    if dry_run:
        print('[dry-run] 跳过 git commit/push')
        return
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full = '[auto] {} · {}'.format(message, stamp)
    try:
        subprocess.check_call(['git', 'add', 'content.json'], cwd=ROOT)
        # 没有变更时 commit 会返回非 0，这里视为正常
        result = subprocess.call(['git', 'commit', '-m', full], cwd=ROOT)
        if result == 0:
            # 显式指定远程与分支，不依赖 upstream 配置（定时任务环境常无 upstream）
            subprocess.check_call(['git', 'push', 'origin', 'HEAD:main'], cwd=ROOT)
            print('[ok] 已提交并推送：' + full)
        else:
            print('[info] 无内容变更，跳过提交')
    except subprocess.CalledProcessError as e:
        print('[error] git 操作失败：{}'.format(e), file=sys.stderr)
        print('[hint] 确认已 git init、已配置 remote，且有推送权限。', file=sys.stderr)
        sys.exit(2)


def cloudflare_deploy(dry_run=False):
    """调用 Direct Upload 部署脚本，把最新静态文件推到 Cloudflare Pages。"""
    if dry_run:
        print('[dry-run] 跳过 Cloudflare 部署')
        return
    deploy_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deploy.py')
    py = sys.executable
    # 当前解释器若无 blake3，自动回退到带依赖的 D:/Python314/python.exe
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
        # 允许全局开关写在子命令之后（定时任务/AI 常把参数放在末尾）
        sp.add_argument('--push', action='store_true', help='写入后自动 git commit/push')
        sp.add_argument('--deploy', action='store_true', help='写入后自动部署到 Cloudflare Pages')
        sp.add_argument('--dry-run', action='store_true', help='只打印操作，不写入不推送')

    sp = sub.add_parser('add-post', help='新增文章')
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

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    data = load_content()
    handlers = {
        'add-post': cmd_add_post,
        'add-business': cmd_add_business,
        'add-listing': cmd_add_listing,
        'set-site': cmd_set_site
    }
    message = handlers[args.command](data, args)
    save_content(data, dry_run=args.dry_run)
    if getattr(args, 'push', False):
        git_push(message, dry_run=args.dry_run)
    if getattr(args, 'deploy', False):
        cloudflare_deploy(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
