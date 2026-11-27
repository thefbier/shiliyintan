# -*- coding: utf-8 -*-
"""GitHub Contents API 逐文件同步（本机直连不稳时的兜底通道）"""
import base64, io, json, subprocess, sys, urllib.request

FILES = ['content.json', 'host.json', 'community.json', 'index.html',
         'assets/app.js', 'assets/style.css']
REPO = 'thefbier/shiliyintan'

def get_token():
    r = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                       capture_output=True, text=True, timeout=30)
    for line in r.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    sys.exit('NO_TOKEN')

def api(method, path, token, body=None):
    hdr = {'Authorization': 'token ' + token, 'Accept': 'application/vnd.github+json',
           'User-Agent': 'sync-script'}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request('https://api.github.com' + path, data=data, headers=hdr, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

token = get_token()
for f in FILES:
    content = base64.b64encode(io.open(f, 'rb').read()).decode()
    sha = None
    try:
        sha = api('GET', f'/repos/{REPO}/contents/{f}?ref=main', token)['sha']
    except Exception:
        pass
    body = {'message': '[sync] update ' + f, 'content': content, 'branch': 'main'}
    if sha:
        body['sha'] = sha
    r = api('PUT', f'/repos/{REPO}/contents/{f}', token, body)
    print('[ok]', f, '->', r['content']['sha'][:8])
