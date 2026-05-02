#!/usr/bin/env python3
“””
gh_push.py — Push SGHv119 files to GitHub via REST API.
No git install required. Works in a-Shell, iSH, or any Python 3.6+.

Usage:
export GH_TOKEN=ghp_your_personal_access_token_here
python3 gh_push.py

Token needs: repo (read+write) scope.
Create one at: https://github.com/settings/tokens/new
“””

import os, sys, json, base64, hashlib
import urllib.request, urllib.error
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

REPO  = ‘Sovereignty-One/SuperGrok-Heavy-4-2-Skeleton’
BRANCH = ‘main’   # change to ‘master’ if needed
TOKEN  = os.environ.get(‘GH_TOKEN’, ‘’)

COMMIT_MSG = (
’SGHv119 v6: port fix 9899(WS)/9897(Python)/9898(KODER), ’
’CodeMaster iOS, key rotation, Fix All button, SG_AGENT shim, ’
‘KC refresh 8080, PG 5432, Redis 6379, throttle clear, bridge.py v4.1, server.js’
)

# ── Files to push ────────────────────────────────────────────────────────────

# Format: (local_path, github_path)

HOME = Path.home()
SCRIPT_DIR = Path(**file**).parent

def find_file(names):
“”“Search common locations for a file.”””
search_dirs = [SCRIPT_DIR, HOME, Path.cwd(),
HOME / ‘Downloads’, HOME / ‘Documents’,
Path(’/mnt/user-data/outputs’)]
for name in names:
for d in search_dirs:
p = d / name
if p.exists():
return p
return None

FILES = [
(find_file([‘SGHv119_v6_FIXED.html’, ‘SGHv119.html’, ‘SGHv119_fixed.html’]), ‘SGHv119.html’),
(find_file([‘bridge.py’, ‘sghv119bridge.py’]),                                ‘bridge.py’),
(find_file([‘server.js’]),                                                     ‘server.js’),
]

# ── GitHub API helpers ────────────────────────────────────────────────────────

API = ‘https://api.github.com’

def gh_req(method, path, body=None):
if not TOKEN:
print(‘❌ GH_TOKEN not set — export GH_TOKEN=ghp_…’)
sys.exit(1)
url  = API + path
data = json.dumps(body).encode() if body else None
req  = urllib.request.Request(url, data=data, method=method, headers={
‘Authorization’: f’Bearer {TOKEN}’,
‘Accept’:        ‘application/vnd.github+json’,
‘X-GitHub-Api-Version’: ‘2022-11-28’,
‘Content-Type’:  ‘application/json’,
‘User-Agent’:    ‘SGHv119-push/1.0’,
})
try:
with urllib.request.urlopen(req, timeout=60) as r:
return json.loads(r.read()), r.status
except urllib.error.HTTPError as e:
body_txt = e.read().decode()[:400]
return {‘error’: body_txt, ‘code’: e.code}, e.code

def get_branch_sha():
“”“Get the latest commit SHA on the target branch.”””
data, status = gh_req(‘GET’, f’/repos/{REPO}/git/ref/heads/{BRANCH}’)
if status == 200:
return data[‘object’][‘sha’]
# Branch doesn’t exist yet — get default branch
data2, s2 = gh_req(‘GET’, f’/repos/{REPO}’)
if s2 == 200:
default = data2.get(‘default_branch’, ‘main’)
data3, s3 = gh_req(‘GET’, f’/repos/{REPO}/git/ref/heads/{default}’)
if s3 == 200:
return data3[‘object’][‘sha’]
print(f’❌ Cannot get branch SHA: {status} — {data}’)
sys.exit(1)

def get_file_sha(github_path):
“”“Get existing file SHA if it exists (needed for updates).”””
data, status = gh_req(‘GET’, f’/repos/{REPO}/contents/{github_path}?ref={BRANCH}’)
if status == 200 and ‘sha’ in data:
return data[‘sha’]
return None

def push_file(local_path, github_path, file_sha=None):
“”“Create or update a single file via Contents API.”””
if local_path is None or not Path(local_path).exists():
print(f’  ⚠  SKIP {github_path} — local file not found’)
return False

```
content = Path(local_path).read_bytes()
b64     = base64.b64encode(content).decode()
size_kb = len(content) / 1024

body = {
    'message': COMMIT_MSG,
    'content': b64,
    'branch':  BRANCH,
}
if file_sha:
    body['sha'] = file_sha   # required for updates

print(f'  → Pushing {github_path} ({size_kb:.0f} KB)...', end=' ', flush=True)
data, status = gh_req('PUT', f'/repos/{REPO}/contents/{github_path}', body)

if status in (200, 201):
    action = 'updated' if file_sha else 'created'
    url    = data.get('content', {}).get('html_url', '')
    print(f'✅ {action}')
    print(f'     {url}')
    return True
else:
    print(f'❌ {status}')
    print(f'     {data.get("error", data)[:200]}')
    return False
```

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
print(’=’ * 60)
print(’  SGHv119 → GitHub Push’)
print(f’  Repo  : {REPO}’)
print(f’  Branch: {BRANCH}’)
print(’=’ * 60)

```
if not TOKEN:
    print('\n❌ GH_TOKEN not set.')
    print('   1. Go to: https://github.com/settings/tokens/new')
    print('   2. Tick the "repo" scope')
    print('   3. Run: export GH_TOKEN=ghp_your_token_here')
    print('   4. python3 gh_push.py\n')
    sys.exit(1)

# Verify repo access
print('\n[1/4] Verifying repo access...')
repo_data, repo_status = gh_req('GET', f'/repos/{REPO}')
if repo_status != 200:
    print(f'❌ Cannot access repo ({repo_status}): {repo_data.get("error","")[:200]}')
    print(f'   Check that the repo exists and your token has access.')
    sys.exit(1)
print(f'  ✅ {repo_data.get("full_name")} — {repo_data.get("visibility","?")} — '
      f'{repo_data.get("default_branch")} branch')

print(f'\n[2/4] Getting {BRANCH} branch SHA...')
branch_sha = get_branch_sha()
print(f'  ✅ HEAD: {branch_sha[:12]}…')

print(f'\n[3/4] Checking for existing files...')
file_shas = {}
for local_path, github_path in FILES:
    sha = get_file_sha(github_path)
    file_shas[github_path] = sha
    status_str = f'exists (will update, sha={sha[:8]}…)' if sha else 'new file'
    print(f'  {github_path}: {status_str}')

print(f'\n[4/4] Pushing {len(FILES)} files...')
results = []
for local_path, github_path in FILES:
    ok = push_file(local_path, github_path, file_shas.get(github_path))
    results.append((github_path, ok))

print('\n' + '=' * 60)
print('  PUSH SUMMARY')
print('=' * 60)
ok_count = sum(1 for _, ok in results if ok)
for gp, ok in results:
    icon = '✅' if ok else '❌'
    print(f'  {icon} {gp}')
print()
print(f'  {ok_count}/{len(results)} files pushed successfully')
print(f'  Repo: https://github.com/{REPO}')
print(f'  Branch: {BRANCH}')
if ok_count > 0:
    print(f'\n  View: https://github.com/{REPO}/blob/{BRANCH}/SGHv119.html')
print('=' * 60)

if ok_count < len(results):
    sys.exit(1)
```

if **name** == ‘**main**’:
main()
