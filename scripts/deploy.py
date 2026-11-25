# -*- coding: utf-8 -*-
"""shiliyintan.cn 静态站 Cloudflare Pages Direct Upload 部署脚本。

用法：
  python scripts/deploy.py                  # 默认部署站点根目录
  python scripts/deploy.py --dry-run        # 只列出将上传的文件，不上传
  python scripts/deploy.py --token-file X   # 指定凭据文件

凭据：默认读 C:/Users/Administrator/.shiliyintan_cf_token；
      不存在则回退读 C:/Users/Administrator/.dressodm_cf_token（同一 Cloudflare 账号的永久 Token）。
      删除凭据文件即停用部署（报 NEED_TOKEN，不硬失败）。
"""
import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

try:
    import blake3
except ImportError:
    sys.exit("NEED_DEP: 缺少 blake3，请用 D:/Python314/python.exe 运行本脚本")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://api.cloudflare.com/client/v4"
ACCT = "3989810367253b6d5373b6e80c21f0d8"
PROJECT = "shiliyintan"
BRANCH = "main"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {"node_modules", ".git", ".wrangler", "__pycache__", ".workbuddy", "scripts"}
SKIP_FILES = {"_worker.js", "_routes.json", "deploy.py", "README.md", "CNAME"}


def load_token(path=None):
    candidates = [path] if path else [
        r"C:/Users/Administrator/.shiliyintan_cf_token",
        r"C:/Users/Administrator/.dressodm_cf_token",
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            t = io.open(p, encoding="utf-8").read().strip()
            if t:
                return t
    sys.exit("NEED_TOKEN: 没找到凭据文件（.shiliyintan_cf_token 或 .dressodm_cf_token）")


def req(method, path, token, body=None, headers=None, retries=6, timeout=90):
    hdr = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    if headers:
        hdr.update(headers)
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
    for i in range(retries):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(API + path, data=data, headers=hdr, method=method),
                timeout=timeout)
            return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 * (i + 1))


def file_hash(data, ext):
    return blake3.blake3((base64.b64encode(data).decode() + ext).encode()).hexdigest()[:32]


def collect_files():
    payload, manifest = [], {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f in SKIP_FILES or f.endswith(".pyc"):
                continue
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            data = open(full, "rb").read()
            ext = os.path.splitext(f)[1][1:]
            h = file_hash(data, ext)
            ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
            payload.append({
                "key": h,
                "value": base64.b64encode(data).decode(),
                "metadata": {"contentType": ctype},
                "base64": True,
            })
            manifest["/" + rel] = h
    return payload, manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-file", help="指定 token 凭据文件路径")
    ap.add_argument("--dry-run", action="store_true", help="只列出文件，不上传")
    args = ap.parse_args()

    payload, manifest = collect_files()
    print("site root:", ROOT)
    print("files:", len(payload), "| manifest:", len(manifest))
    if args.dry_run:
        for k in sorted(manifest):
            print("  ", k)
        return

    token = load_token(args.token_file)

    print("== 1. upload token ==")
    s, b = req("GET", f"/accounts/{ACCT}/pages/projects/{PROJECT}/upload-token", token)
    j = json.loads(b)
    if not j.get("success"):
        print("UPLOAD_TOKEN_FAIL", s, b[:400]); sys.exit(1)
    jwt = j["result"]["jwt"]
    JH = {"Authorization": "Bearer " + jwt, "Content-Type": "application/json"}

    def jreq(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for i in range(8):
            try:
                r = urllib.request.urlopen(
                    urllib.request.Request(API + path, data=data, headers=JH, method=method), timeout=90)
                return r.status, r.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()
            except Exception:
                if i == 7:
                    raise
                time.sleep(2 * (i + 1))

    print("== 2. check-missing ==")
    s, b = jreq("POST", "/pages/assets/check-missing", {"hashes": [p["key"] for p in payload]})
    if s == 200:
        missing = set(json.loads(b).get("result", []))
        payload = [p for p in payload if p["key"] in missing]
    print("  to upload:", len(payload))

    if payload:
        s, b = jreq("POST", "/pages/assets/upload", payload)
        if s != 200:
            print("UPLOAD_FAIL", s, b[:300]); sys.exit(1)
        print("  uploaded:", s)

    s, b = jreq("POST", "/pages/assets/upsert-hashes", {"hashes": list(manifest.values())})
    print("  upsert-hashes:", s)

    print("== 3. create deployment ==")
    boundary = "----CF" + os.urandom(8).hex()
    fields = [
        ("manifest", json.dumps(manifest, ensure_ascii=False).encode(), None, None),
        ("branch", BRANCH.encode(), None, None),
    ]
    buf = io.BytesIO()
    for name, value, filename, ctype in fields:
        buf.write(f"--{boundary}\r\n".encode())
        cd = f'Content-Disposition: form-data; name="{name}"'
        if filename:
            cd += f'; filename="{filename}"'
        buf.write((cd + "\r\n").encode())
        if ctype:
            buf.write(f"Content-Type: {ctype}\r\n".encode())
        buf.write(b"\r\n")
        buf.write(value)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())

    s, b = req("POST", f"/accounts/{ACCT}/pages/projects/{PROJECT}/deployments",
               token, body=buf.getvalue(),
               headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
               retries=8, timeout=120)
    try:
        j = json.loads(b)
    except Exception:
        print("DEPLOY_FAIL raw:", b[:500]); sys.exit(1)
    if j.get("success"):
        r = j["result"]
        print("DEPLOY_OK", r.get("id"), r.get("url"), r.get("environment"))
    else:
        print("DEPLOY_FAIL", s, b[:800]); sys.exit(1)


if __name__ == "__main__":
    main()
