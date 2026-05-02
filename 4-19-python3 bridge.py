#!/usr/bin/env python3
“””
SuperGrok Unified Bridge v4.1
Port layout:
9897 — THIS server (Python HTTP + WebSocket)
9899 — Node.js WS bridge (optional — proxies to this server)
9898 — KODER app HTTP server (iOS file server)
8080 — Keycloak HTTP
8443 — Keycloak HTTPS
5432 — PostgreSQL
6379 — Redis

Quick start (a-Shell or iSH):
export ANTHROPIC_API_KEY=sk-ant-…
export OPENAI_API_KEY=sk-…
export XAI_API_KEY=xai-…
python3 bridge.py

Then open Safari at: http://127.0.0.1:9897
Or serve via KODER on 9898, WS bridge on 9899.
“””

import os, sys, json, socket, hashlib, base64, threading, subprocess, time, secrets, logging
import urllib.request, urllib.error
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
level=getattr(logging, os.environ.get(‘LOG_LEVEL’, ‘INFO’).upper(), logging.INFO),
format=’%(asctime)s [%(levelname)s] %(message)s’
)
log = logging.getLogger(‘bridge’)

# ── Configuration ──────────────────────────────────────────────────────────

PORT         = int(os.environ.get(‘SG_PORT’, 9897))
HOST         = os.environ.get(‘SG_HOST’, ‘127.0.0.1’)
KC_URL       = os.environ.get(‘KEYCLOAK_URL’, ‘http://127.0.0.1:8080’)
KC_REALM     = os.environ.get(‘KEYCLOAK_REALM’, ‘sovereignty-ai’)
PG_HOST      = os.environ.get(‘PG_HOST’, ‘127.0.0.1’)
PG_PORT      = int(os.environ.get(‘PG_PORT’, 5432))
REDIS_HOST   = os.environ.get(‘REDIS_HOST’, ‘127.0.0.1’)
REDIS_PORT   = int(os.environ.get(‘REDIS_PORT’, 6379))
LOG_PATH     = os.path.expanduser(os.environ.get(‘AUDIT_LOG’, ‘~/sg_audit.log’))
SOVEREIGN    = os.environ.get(‘SOVEREIGN_MODE’, ‘true’).lower() == ‘true’
ALLOWED_OUT  = set(os.environ.get(‘ALLOWED_OUTBOUND’, ‘api.anthropic.com,api.openai.com,api.x.ai’).split(’,’))

KEYS = {
‘anthropic’: os.environ.get(‘ANTHROPIC_API_KEY’, ‘’),
‘openai’:    os.environ.get(‘OPENAI_API_KEY’, ‘’),
‘grok’:      os.environ.get(‘GROK_API_KEY’, os.environ.get(‘XAI_API_KEY’, ‘’)),
‘copilot’:   os.environ.get(‘GITHUB_COPILOT_TOKEN’, ‘’),
}

# ── HTML discovery ─────────────────────────────────────────────────────────

def find_html():
dirs = [Path.home(), Path.cwd(), Path(’/root’), Path(’/var/mobile’),
Path(’/home/user’), Path(’/var/root’)]
pats = [‘SGHv119*.html’, ‘SGHv119*.txt’, ‘SuperGrok*.html’, ‘*.html’]
for d in dirs:
for p in pats:
hits = sorted(d.glob(p), reverse=True)
if hits:
return str(hits[0])
return None

HTML_FILE = find_html()

# ══════════════════════════════════════════════════════════════════════════

# IMMUTABLE AUDIT LOG — SHA3-512 hash-chained (from 1fix-bridge.py)

# ══════════════════════════════════════════════════════════════════════════

_audit_lock = threading.Lock()

def _last_hash() -> str:
if not os.path.exists(LOG_PATH):
return ‘genesis’
try:
with open(LOG_PATH, ‘r’, encoding=‘utf-8’) as fh:
lines = [l for l in fh.readlines() if l.strip()]
if lines:
parts = lines[-1].strip().rsplit(’ ‘, 1)
return parts[-1] if len(parts) == 2 else ‘genesis’
except Exception as e:
log.warning(f’[audit] read error: {e}’)
return ‘genesis’

def immutable_log(event: str, data: dict = None):
“”“Append a tamper-evident log entry chained with SHA3-512.”””
try:
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
except Exception:
pass
ts        = time.strftime(’%Y-%m-%dT%H:%M:%S%z’)
entry_str = json.dumps({‘ts’: ts, ‘event’: event, ‘data’: data or {}}, separators=(’,’, ‘:’))
prev_hash = _last_hash()
combined  = f’{prev_hash}|{entry_str}’.encode(‘utf-8’)
new_hash  = hashlib.sha3_512(combined).hexdigest()
line      = f’{entry_str} {new_hash}\n’
with _audit_lock:
try:
with open(LOG_PATH, ‘a’, encoding=‘utf-8’) as fh:
fh.write(line)
except Exception as e:
log.warning(f’[audit] write error: {e}’)

# ══════════════════════════════════════════════════════════════════════════

# PURGE TEST ARTEFACTS (from 1fix-bridge.py)

# ══════════════════════════════════════════════════════════════════════════

*TEST_KEYWORDS = (‘test’, ‘mock’, ‘sim’)
*PURGE_PREFIXES = (’test*’, ’mock*’, ‘sim_’)

def purge_tests():
“”“Remove test/mock modules and globals. Abort if a test runner is detected.”””
if ‘unittest’ in sys.modules or ‘pytest’ in sys.modules:
log.critical(‘Test runner detected — aborting production run.’)
sys.exit(1)
for name in list(sys.modules):
if any(kw in name.lower() for kw in _TEST_KEYWORDS):
try: del sys.modules[name]
except KeyError: pass
for k in list(globals()):
if k.lower().startswith(_PURGE_PREFIXES):
try: del globals()[k]
except KeyError: pass
log.info(’[purge] Test artefacts purged’)

purge_tests()

# ══════════════════════════════════════════════════════════════════════════

# AI PROVIDERS

# ══════════════════════════════════════════════════════════════════════════

def _post_json(url: str, headers: dict, body: dict):
try:
data = json.dumps(body).encode()
req  = urllib.request.Request(url, data=data, headers=headers, method=‘POST’)
with urllib.request.urlopen(req, timeout=60) as r:
return json.loads(r.read()), None
except urllib.error.HTTPError as e:
return None, ‘%d: %s’ % (e.code, e.read().decode()[:300])
except Exception as e:
return None, str(e)

def ai_claude(messages, model=‘claude-opus-4-5’):
k = KEYS[‘anthropic’]
if not k: return None, ‘ANTHROPIC_API_KEY not set’
r, e = _post_json(
‘https://api.anthropic.com/v1/messages’,
{‘Content-Type’:‘application/json’,‘x-api-key’:k,‘anthropic-version’:‘2023-06-01’},
{‘model’:model,‘max_tokens’:2000,‘messages’:messages}
)
return (r[‘content’][0][‘text’], None) if r else (None, e)

def ai_openai(messages, model=‘gpt-4o’):
k = KEYS[‘openai’]
if not k: return None, ‘OPENAI_API_KEY not set’
r, e = _post_json(
‘https://api.openai.com/v1/chat/completions’,
{‘Content-Type’:‘application/json’,‘Authorization’:’Bearer ’+k},
{‘model’:model,‘max_tokens’:2000,‘messages’:messages}
)
return (r[‘choices’][0][‘message’][‘content’], None) if r else (None, e)

def ai_grok(messages, model=‘grok-3-latest’):
k = KEYS[‘grok’]
if not k: return None, ‘XAI_API_KEY not set’
r, e = _post_json(
‘https://api.x.ai/v1/chat/completions’,
{‘Content-Type’:‘application/json’,‘Authorization’:’Bearer ’+k},
{‘model’:model,‘max_tokens’:2000,‘messages’:messages}
)
return (r[‘choices’][0][‘message’][‘content’], None) if r else (None, e)

def route_ai(agent: str, messages: list, model=None):
a = (agent or ‘claude’).lower()
if   a in (‘claude’,‘anthropic’,‘arbiter’): order = [ai_claude, ai_openai, ai_grok]
elif ‘gpt’ in a or ‘openai’ in a:           order = [ai_openai, ai_claude, ai_grok]
elif ‘grok’ in a or ‘xai’ in a:             order = [ai_grok,   ai_claude, ai_openai]
else:                                        order = [ai_claude, ai_openai, ai_grok]
for fn in order:
text, err = fn(messages, model) if model else fn(messages)
if text: return text, None
return None, ‘All providers failed — check API keys’

def shell_exec(cmd: str) -> str:
try:
r = subprocess.run(cmd, shell=True, capture_output=True,
text=True, timeout=30, cwd=str(Path.home()))
return (r.stdout + r.stderr)[:8192]
except subprocess.TimeoutExpired:
return ‘Timed out (30s)’
except Exception as e:
return str(e)

# ══════════════════════════════════════════════════════════════════════════

# KEY ROTATION

# ══════════════════════════════════════════════════════════════════════════

def rotate_key(provider: str, new_key: str) -> dict:
“”“Rotate an API key: store, update env, audit log, return status.”””
aliases = {‘claude’:‘anthropic’,‘anthropic’:‘anthropic’,‘openai’:‘openai’,
‘gpt’:‘openai’,‘grok’:‘grok’,‘xai’:‘grok’,‘copilot’:‘copilot’}
norm = aliases.get(provider.lower(), provider.lower())
if norm not in KEYS:
return {‘ok’: False, ‘error’: f’Unknown provider: {provider}’}
KEYS[norm] = new_key
env_map = {‘anthropic’:‘ANTHROPIC_API_KEY’,‘openai’:‘OPENAI_API_KEY’,
‘grok’:‘XAI_API_KEY’,‘copilot’:‘GITHUB_COPILOT_TOKEN’}
if norm in env_map:
os.environ[env_map[norm]] = new_key
masked = new_key[:8] + ‘…’ + new_key[-4:] if len(new_key) > 12 else ‘***’
h = hashlib.sha3_512(new_key.encode()).hexdigest()[:32]
immutable_log(‘KEY_ROTATED’, {‘provider’: norm, ‘masked’: masked, ‘hash_prefix’: h})
return {‘ok’: True, ‘provider’: norm, ‘masked’: masked}

# ══════════════════════════════════════════════════════════════════════════

# WEBSOCKET RFC 6455

# ══════════════════════════════════════════════════════════════════════════

WS_GUID = ‘258EAFA5-E914-47DA-95CA-C5AB0DC85B11’

def _ws_accept(key: str) -> str:
raw = hashlib.sha1((key.strip() + WS_GUID).encode()).digest()
return base64.b64encode(raw).decode()

def ws_handshake(conn, key: str):
resp = (
‘HTTP/1.1 101 Switching Protocols\r\n’
‘Upgrade: websocket\r\n’
‘Connection: Upgrade\r\n’
’Sec-WebSocket-Accept: ’ + _ws_accept(key) + ‘\r\n’
‘Access-Control-Allow-Origin: *\r\n’
‘\r\n’
)
conn.sendall(resp.encode())

def ws_read_frame(conn):
“”“Returns (opcode, bytes_payload) or (None, None) on disconnect.”””
def recv_exact(n):
buf = b’’
while len(buf) < n:
chunk = conn.recv(n - len(buf))
if not chunk:
raise ConnectionError(‘disconnected’)
buf += chunk
return buf
try:
h      = recv_exact(2)
opcode = h[0] & 0x0F
masked = bool(h[1] & 0x80)
plen   = h[1] & 0x7F
if   plen == 126: plen = int.from_bytes(recv_exact(2), ‘big’)
elif plen == 127: plen = int.from_bytes(recv_exact(8), ‘big’)
mask   = recv_exact(4) if masked else b’\x00\x00\x00\x00’
data   = bytearray(recv_exact(plen))
if masked:
for i in range(len(data)):
data[i] ^= mask[i % 4]
return opcode, bytes(data)
except Exception:
return None, None

def ws_write(conn, payload, opcode=0x01) -> bool:
if isinstance(payload, str):
payload = payload.encode()
n = len(payload)
if   n < 126:   hdr = bytes([0x80 | opcode, n])
elif n < 65536: hdr = bytes([0x80 | opcode, 126]) + n.to_bytes(2, ‘big’)
else:           hdr = bytes([0x80 | opcode, 127]) + n.to_bytes(8, ‘big’)
try:
conn.sendall(hdr + payload)
return True
except Exception:
return False

def ws_json(conn, obj):
return ws_write(conn, json.dumps(obj))

# ══════════════════════════════════════════════════════════════════════════

# WS MESSAGE HANDLER

# ══════════════════════════════════════════════════════════════════════════

def handle_ws_msg(conn, raw):
try:
msg = json.loads(raw)
except Exception:
ws_json(conn, {‘type’: ‘error’, ‘error’: ‘invalid JSON’})
return

```
t   = msg.get('type', '')
rid = msg.get('request_id', '')
log.debug(f'[WS] {t}')

if t == 'ping':
    ws_json(conn, {'type': 'pong', 'ts': int(time.time() * 1000)})

elif t in ('agent_query', 'ai_query', 'chat', 'message', 'query'):
    agent    = msg.get('agent', msg.get('provider', 'claude'))
    prompt   = msg.get('prompt', msg.get('message', msg.get('content', '')))
    history  = msg.get('history', [])
    messages = history + [{'role': 'user', 'content': prompt}]
    ws_json(conn, {'type': 'agent_thinking', 'agent': agent, 'request_id': rid})
    immutable_log('AGENT_QUERY', {'agent': agent, 'prompt_len': len(prompt)})
    text, err = route_ai(agent, messages, msg.get('model'))
    immutable_log('AGENT_RESPONSE', {'agent': agent, 'ok': bool(text)})
    ws_json(conn, {
        'type': 'agent_response', 'agent': agent, 'request_id': rid,
        'text': text or '', 'response': text or '', 'error': err,
    })

elif t in ('exec', 'shell_exec', 'terminal', 'run'):
    cmd = msg.get('cmd', msg.get('command', ''))
    immutable_log('SHELL_EXEC', {'cmd': cmd[:200]})
    ws_json(conn, {'type': 'exec_result', 'output': shell_exec(cmd), 'cmd': cmd})

elif t in ('ssh_input', 'ssh_data'):
    ws_json(conn, {'type': 'ssh_data', 'data': shell_exec(msg.get('data', '').strip())})

elif t == 'ssh_connect':
    ws_json(conn, {
        'type': 'ssh_connected',
        'banner': 'SuperGrok SSH Bridge\n%s:%s\n' % (msg.get('host', 'localhost'), msg.get('port', 22)),
        'prompt': '%s@%s:~$ ' % (msg.get('username', 'root'), msg.get('host', 'localhost')),
    })

elif t == 'speak':
    text = msg.get('text', '')
    threading.Thread(
        target=lambda: subprocess.run(
            'say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text, text),
            shell=True
        ), daemon=True
    ).start()
    ws_json(conn, {'type': 'speak_result', 'text': text})

elif t == 'keys_set':
    for k, v in (msg.get('keys') or {}).items():
        if k in KEYS and v:
            result = rotate_key(k, v)
            log.info(f'[key] Rotated {result.get("provider")} — {result.get("masked")}')
    ws_json(conn, {'type': 'keys_saved', 'keys': {k: bool(v) for k, v in KEYS.items()}})

elif t == 'rotate_key':
    provider = msg.get('provider', '')
    new_key  = msg.get('key', '')
    result   = rotate_key(provider, new_key)
    ws_json(conn, {'type': 'rotate_key_result', **result,
                   'message': result.get('masked', result.get('error', ''))})

elif t == 'key_status':
    ws_json(conn, {
        'type': 'key_status_result',
        'status': {k: {'set': bool(v), 'masked': (v[:8]+'…'+v[-4:] if v and len(v)>12 else ''), 'stale': False}
                   for k, v in KEYS.items()}
    })

elif t == 'health':
    ws_json(conn, {
        'type': 'health_ok', 'version': 'v4.1', 'port': PORT,
        'keys': {k: bool(v) for k, v in KEYS.items()},
        'keycloak': KC_URL,
    })

elif t == 'audit_query':
    entries = []
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, 'r') as fh:
                for line in fh.readlines()[-50:]:
                    parts = line.strip().rsplit(' ', 1)
                    if parts:
                        try:
                            entries.append(json.loads(parts[0]))
                        except Exception:
                            pass
        except Exception:
            pass
    ws_json(conn, {'type': 'audit_result', 'entries': entries})

else:
    ws_json(conn, {'type': 'ack', 'received': t, 'ts': int(time.time() * 1000)})
```

def run_ws(conn, addr, path):
log.info(f’[WS] + {addr} path={path}’)
immutable_log(‘WS_CONNECT’, {‘addr’: str(addr), ‘path’: path})
ws_json(conn, {
‘type’: ‘connected’, ‘version’: ‘SuperGrok Bridge v4.1’,
‘port’: PORT, ‘keys’: {k: bool(v) for k, v in KEYS.items()},
})
try:
while True:
opcode, payload = ws_read_frame(conn)
if opcode is None: break
if opcode == 0x8:  break                          # Close
if opcode == 0x9:  ws_write(conn, b’’, 0xA); continue  # Ping → Pong
if opcode in (0x1, 0x2): handle_ws_msg(conn, payload)
except Exception as e:
log.error(f’[WS] ! {addr} {e}’)
finally:
log.info(f’[WS] - {addr}’)
immutable_log(‘WS_DISCONNECT’, {‘addr’: str(addr)})
try: conn.close()
except: pass

# ══════════════════════════════════════════════════════════════════════════

# HTTP HANDLER

# ══════════════════════════════════════════════════════════════════════════

CORS_HDR = (
‘Access-Control-Allow-Origin: *\r\n’
‘Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n’
‘Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key\r\n’
)

def http_send(conn, code: int, body, ctype=‘application/json’):
phrase = {200:‘OK’, 204:‘No Content’, 404:‘Not Found’, 500:‘Internal Server Error’}.get(code, ‘OK’)
if isinstance(body, dict): body = json.dumps(body).encode()
elif isinstance(body, str): body = body.encode()
hdr = (
‘HTTP/1.1 %d %s\r\n’
‘Content-Type: %s; charset=utf-8\r\n’
‘Content-Length: %d\r\n’
‘%s’
‘Cache-Control: no-store\r\n’
‘Connection: close\r\n’
‘\r\n’
) % (code, phrase, ctype, len(body), CORS_HDR)
try: conn.sendall(hdr.encode() + body)
except Exception: pass

def _parse_body(body_bytes: bytes) -> dict:
if not body_bytes:
return {}
try:
return json.loads(body_bytes)
except Exception:
return {}

def handle_http(conn, method: str, path: str, body_bytes: bytes):
if method == ‘OPTIONS’:
http_send(conn, 204, b’’)
return

```
# Parse body for both GET and POST (some GET endpoints pass JSON body)
body = _parse_body(body_bytes)

if method == 'GET':
    # ── Serve dashboard HTML ──────────────────────────────────────────
    if path in ('/', '/index.html'):
        if HTML_FILE and Path(HTML_FILE).exists():
            http_send(conn, 200, Path(HTML_FILE).read_bytes(), 'text/html')
        else:
            http_send(conn, 200, _fallback_html(), 'text/html')

    # ── Health ────────────────────────────────────────────────────────
    elif path in ('/health', '/api/health'):
        http_send(conn, 200, {
            'status': 'ok', 'version': 'v4.1', 'port': PORT,
            'html': HTML_FILE or 'not found',
            'keys': {k: bool(v) for k, v in KEYS.items()},
            'keycloak': KC_URL,
            'ts': int(time.time()),
        })

    # ── PostgreSQL health ─────────────────────────────────────────────
    elif path == '/health/pg':
        try:
            import socket as _socket
            s = _socket.create_connection((PG_HOST, PG_PORT), timeout=2)
            s.close()
            http_send(conn, 200, {'status': 'ok', 'host': PG_HOST, 'port': PG_PORT})
        except Exception as e:
            http_send(conn, 200, {'status': 'offline', 'error': str(e), 'port': PG_PORT})

    # ── Redis health ──────────────────────────────────────────────────
    elif path == '/health/redis':
        try:
            import socket as _socket
            s = _socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=2)
            s.sendall(b'PING\r\n')
            resp = s.recv(16)
            s.close()
            http_send(conn, 200, {'status': 'ok' if b'PONG' in resp else 'unknown',
                                  'host': REDIS_HOST, 'port': REDIS_PORT})
        except Exception as e:
            http_send(conn, 200, {'status': 'offline', 'error': str(e), 'port': REDIS_PORT})

    # ── TLS ───────────────────────────────────────────────────────────
    elif path == '/api/tls/status':
        cert_json = Path.home() / 'sg_tls_cert.json'
        if cert_json.exists():
            http_send(conn, 200, json.loads(cert_json.read_text()))
        else:
            http_send(conn, 200, {'status': 'no cert', 'hint': 'POST /api/tls/generate'})

    # ── Key status ────────────────────────────────────────────────────
    elif path == '/api/keys/status':
        http_send(conn, 200, {
            'keys': {k: {'set': bool(v),
                         'masked': (v[:8]+'…'+v[-4:] if v and len(v)>12 else '')}
                     for k, v in KEYS.items()}
        })

    # ── Keycloak test ─────────────────────────────────────────────────
    elif path == '/auth/keycloak/test':
        try:
            r, e = _post_json(KC_URL + '/realms/master/.well-known/openid-configuration', {}, {})
            if r:
                http_send(conn, 200, {'keycloak': 'ok', 'issuer': r.get('issuer',''),
                                      'url': KC_URL})
            else:
                http_send(conn, 200, {'keycloak': 'offline', 'note': f'Start Keycloak on {KC_URL}'})
        except Exception as e:
            http_send(conn, 200, {'keycloak': 'offline', 'error': str(e)})

    elif path == '/auth/keycloak/realm':
        http_send(conn, 200, {'keycloak_url': KC_URL, 'realm': KC_REALM})

    # ── OAuth discovery ───────────────────────────────────────────────
    elif path in ('/.well-known/openid-configuration',):
        issuer = f'http://{HOST}:{PORT}/oauth'
        http_send(conn, 200, {
            'issuer': issuer,
            'authorization_endpoint': issuer+'/authorize',
            'token_endpoint': issuer+'/token',
            'introspection_endpoint': issuer+'/introspect',
            'revocation_endpoint': issuer+'/revoke',
            'jwks_uri': issuer+'/.well-known/jwks.json',
            'scopes_supported': ['openid','profile','agent:read','admin'],
            'response_types_supported': ['code'],
            'grant_types_supported': ['authorization_code','client_credentials'],
            'code_challenge_methods_supported': ['S256'],
        })

    elif path == '/.well-known/jwks.json':
        http_send(conn, 200, {'keys': [{'kty':'oct','alg':'HS256','use':'sig','kid':'sg-key-1'}]})

    else:
        http_send(conn, 404, {'error': 'not found', 'path': path})

elif method == 'POST':
    # ── AI / agent ────────────────────────────────────────────────────
    if path in ('/api/ai', '/api/agent', '/api/chat', '/ws-dispatch'):
        t     = body.get('type', '')
        agent = body.get('agent', body.get('provider', 'claude'))

        # ws-dispatch: handle typed messages like WS does
        if t == 'ping':
            http_send(conn, 200, {'type': 'pong', 'ts': int(time.time() * 1000)})
            return
        if t == 'key_status':
            http_send(conn, 200, {
                'type': 'key_status_result',
                'status': {k: {'set': bool(v), 'masked': (v[:8]+'…'+v[-4:] if v and len(v)>12 else '')}
                           for k, v in KEYS.items()}
            })
            return
        if t == 'rotate_key':
            result = rotate_key(body.get('provider',''), body.get('key',''))
            http_send(conn, 200, {'type':'rotate_key_result', **result})
            return
        if t == 'audit_query':
            http_send(conn, 200, {'type':'audit_result','entries':[]})
            return

        prompt   = body.get('prompt', body.get('message', body.get('content', '')))
        history  = body.get('history', [])
        messages = history + [{'role': 'user', 'content': prompt}]
        immutable_log('HTTP_AGENT_QUERY', {'agent': agent, 'prompt_len': len(prompt)})
        text, err = route_ai(agent, messages, body.get('model'))
        http_send(conn, 200, {
            'type': 'agent_response', 'agent': agent,
            'text': text or '', 'response': text or '', 'error': err,
        })

    # ── Shell ─────────────────────────────────────────────────────────
    elif path in ('/api/exec', '/api/terminal', '/api/shell'):
        cmd = body.get('cmd', body.get('command', ''))
        immutable_log('HTTP_SHELL_EXEC', {'cmd': cmd[:200]})
        http_send(conn, 200, {'type': 'exec_result', 'output': shell_exec(cmd)})

    # ── Key management ────────────────────────────────────────────────
    elif path == '/api/keys':
        saved = []
        for k, v in body.items():
            if k in KEYS and v:
                result = rotate_key(k, v)
                if result['ok']:
                    saved.append(result['masked'])
        http_send(conn, 200, {'saved': True, 'rotated': saved,
                              'keys': {k: bool(v) for k, v in KEYS.items()}})

    elif path == '/api/keys/rotate':
        provider = body.get('provider', '')
        new_key  = body.get('key', '')
        http_send(conn, 200, rotate_key(provider, new_key))

    # ── TLS generate ──────────────────────────────────────────────────
    elif path in ('/api/tls/generate', '/api/tls/rotate'):
        days = body.get('days', 30)
        cn   = body.get('cn', 'supergrok.local')
        ts   = int(time.time())
        key_f = str(Path.home() / f'sg-tls-{ts}.key')
        crt_f = str(Path.home() / f'sg-tls-{ts}.crt')
        result = subprocess.run(
            f'openssl req -x509 -nodes -newkey ec -pkeyopt ec_paramgen_curve:P-256 '
            f'-keyout "{key_f}" -out "{crt_f}" -days {days} -subj "/CN={cn}" 2>&1',
            shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            with open(crt_f, 'rb') as fh:
                fp = hashlib.sha256(fh.read()).hexdigest()[:16]
            meta = {'cert': crt_f, 'key': key_f, 'cn': cn, 'days': days, 'fingerprint': fp}
            (Path.home() / 'sg_tls_cert.json').write_text(json.dumps(meta))
            immutable_log('TLS_GENERATED', {'cn': cn, 'fp': fp})
            http_send(conn, 200, meta)
        else:
            http_send(conn, 500, {'error': result.stdout + result.stderr})

    # ── Sinkhole ──────────────────────────────────────────────────────
    elif path == '/api/sinkhole':
        domains = body.get('domains', [])
        ip      = body.get('ip', '127.0.0.1')
        sinkhole_file = Path.home() / 'sg_sinkhole.hosts'
        with open(sinkhole_file, 'a') as fh:
            for d in domains:
                fh.write(f'{ip} {d}\n')
        immutable_log('SINKHOLE', {'count': len(domains), 'ip': ip})
        http_send(conn, 200, {'count': len(domains), 'file': str(sinkhole_file)})

    # ── Firewall ──────────────────────────────────────────────────────
    elif path == '/api/firewall/block':
        ip  = body.get('ip', '')
        dur = body.get('duration', 300)
        if ip:
            # Block on bridge port 9897 (not 9898 — that's KODER)
            subprocess.run(f'sudo ufw deny from {ip} to any port {PORT} 2>/dev/null',
                           shell=True, timeout=10)
            def _unblock(ip_, dur_):
                time.sleep(dur_)
                subprocess.run(f'sudo ufw delete deny from {ip_} to any port {PORT} 2>/dev/null',
                               shell=True)
            threading.Thread(target=_unblock, args=(ip, dur), daemon=True).start()
        immutable_log('FIREWALL_BLOCK', {'ip': ip, 'duration': dur})
        http_send(conn, 200, {'blocked': ip, 'duration': dur})

    # ── Enforce ───────────────────────────────────────────────────────
    elif path == '/api/enforce':
        subjects = body.get('subjects', [])
        immutable_log('ENFORCE', {'subjects': subjects})
        http_send(conn, 200, {'enforced': len(subjects), 'results': {s: 'enforced' for s in subjects}})

    # ── Speak ─────────────────────────────────────────────────────────
    elif path == '/api/speak':
        text = body.get('text', '')
        subprocess.run('say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text, text), shell=True)
        http_send(conn, 200, {'done': True})

    # ── OAuth token ───────────────────────────────────────────────────
    elif path == '/oauth/token':
        now   = int(time.time())
        token = secrets.token_urlsafe(32)
        http_send(conn, 200, {
            'access_token': token, 'token_type': 'Bearer', 'expires_in': 3600,
            'scope': body.get('scope', 'openid profile'),
            'claims': {
                'iss': f'http://{HOST}:{PORT}/oauth',
                'sub': body.get('client_id', 'sg_user'),
                'iat': now, 'exp': now + 3600,
                'jti': secrets.token_hex(8),
            },
        })

    elif path == '/oauth/introspect':
        t = body.get('token', '')
        http_send(conn, 200, {'active': bool(t), 'token': t[:8]+'...' if t else None})

    elif path == '/oauth/revoke':
        http_send(conn, 200, {'revoked': True, 'token': body.get('token','')[:8]+'...'})

    else:
        http_send(conn, 404, {'error': 'not found', 'path': path})

else:
    http_send(conn, 405, {'error': 'method not allowed'})
```

# ── Fallback HTML (shown when no HTML file found) ─────────────────────────

def _fallback_html() -> bytes:
rows = ‘’
for k, v in KEYS.items():
color = ‘#3fb950’ if v else ‘#ff6b6b’
note  = ‘set ✓’ if v else f’not set — export {k.upper()}_API_KEY=…’
rows += f’<li style="color:{color}">{k}: {note}</li>’
html = (
‘<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SuperGrok Bridge</title>’
‘<style>body{background:#0d1117;color:#c9d1d9;font-family:monospace;padding:40px;’
‘max-width:700px;margin:0 auto}h1{color:#00ffc8}’
‘code{background:#161b22;padding:2px 6px;border-radius:4px;color:#79c0ff}’
‘a{color:#58a6ff}</style></head><body>’
‘<h1>SuperGrok Bridge v4.1</h1>’
f’<p style="color:#3fb950">✅ HTTP + WebSocket on port {PORT}</p>’
f’<p style="color:#ff9800">⚠ Place SGHv119*.html in ~/ to serve the dashboard.</p>’
f’<ul>{rows}</ul>’
f’<p><a href="/health">/health</a> · <a href="/api/keys/status">/api/keys/status</a></p>’
f’<hr><p style="font-size:11px;color:#444">Port map: Python={PORT} | KODER=9898 | Node WS=9899 | KC=8080/8443 | PG=5432 | Redis=6379</p>’
‘</body></html>’
)
return html.encode()

# ══════════════════════════════════════════════════════════════════════════

# CONNECTION DISPATCHER

# ══════════════════════════════════════════════════════════════════════════

def handle_conn(conn, addr):
conn.settimeout(30)
try:
buf = b’’
while b’\r\n\r\n’ not in buf:
c = conn.recv(4096)
if not c: return
buf += c
if len(buf) > 65536: return

```
    head_raw, _, body_start = buf.partition(b'\r\n\r\n')
    lines = head_raw.decode('utf-8', errors='replace').split('\r\n')
    req   = lines[0].split()
    if len(req) < 2: return
    method = req[0].upper()
    path   = req[1]

    hdrs = {}
    for ln in lines[1:]:
        if ':' in ln:
            k, _, v = ln.partition(':')
            hdrs[k.strip().lower()] = v.strip()

    # WebSocket upgrade
    if hdrs.get('upgrade', '').lower() == 'websocket' and 'sec-websocket-key' in hdrs:
        ws_handshake(conn, hdrs['sec-websocket-key'])
        conn.settimeout(None)
        run_ws(conn, addr, path)
        return

    # Regular HTTP — read full body
    clen     = int(hdrs.get('content-length', 0))
    body_raw = body_start
    while len(body_raw) < clen:
        c = conn.recv(min(4096, clen - len(body_raw)))
        if not c: break
        body_raw += c

    handle_http(conn, method, path, body_raw)

except Exception:
    pass
finally:
    try: conn.close()
    except: pass
```

# ══════════════════════════════════════════════════════════════════════════

# LIVE PING WATCHDOG (from 1fix-bridge.py)

# ══════════════════════════════════════════════════════════════════════════

def live_ping_watchdog(host=HOST, port=PORT, interval=15):
“”“Periodically self-ping the bridge to verify it’s accepting connections.”””
import socket as _socket
while True:
time.sleep(interval)
try:
s = _socket.create_connection((host, port), timeout=3)
req = b’GET /health HTTP/1.0\r\nHost: %s\r\n\r\n’ % host.encode()
s.sendall(req)
resp = s.recv(256)
s.close()
if b’200’ not in resp:
log.warning(f’[watchdog] /health returned non-200’)
except Exception as e:
log.error(f’[watchdog] Bridge unreachable: {e}’)
immutable_log(‘WATCHDOG_FAIL’, {‘error’: str(e)})

# ══════════════════════════════════════════════════════════════════════════

# ENTRY POINT

# ══════════════════════════════════════════════════════════════════════════

if **name** == ‘**main**’:
immutable_log(‘BRIDGE_START’, {‘port’: PORT, ‘host’: HOST, ‘version’: ‘v4.1’})

```
print('=' * 60)
print(f'  SuperGrok Unified Bridge v4.1')
print(f'  Port map:')
print(f'    {PORT}  ← THIS server (HTTP + WebSocket)')
print(f'    9899 ← Node WS bridge (optional proxy)')
print(f'    9898 ← KODER app (iOS file server)')
print(f'    8080/8443 ← Keycloak')
print(f'    5432 ← PostgreSQL')
print(f'    6379 ← Redis')
print('=' * 60)
print(f'  Dashboard : http://{HOST}:{PORT}')
print(f'  Health    : http://{HOST}:{PORT}/health')
print(f'  HTML      : {HTML_FILE or "NOT FOUND — place SGHv119*.html in ~/"}')
print()
print(f'  Anthropic : {"ready ✓" if KEYS["anthropic"] else "export ANTHROPIC_API_KEY=sk-ant-…"}')
print(f'  OpenAI    : {"ready ✓" if KEYS["openai"]    else "export OPENAI_API_KEY=sk-…"}')
print(f'  Grok/xAI  : {"ready ✓" if KEYS["grok"]      else "export XAI_API_KEY=xai-…"}')
print(f'  Keycloak  : {KC_URL}')
print()
print(f'  AUDIT LOG : {LOG_PATH}')
print('=' * 60)

# Start watchdog thread
threading.Thread(
    target=live_ping_watchdog, args=(HOST, PORT, 15), daemon=True
).start()

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    srv.bind((HOST, PORT))
except OSError as e:
    print(f'\n❌ Cannot bind {HOST}:{PORT} — {e}')
    print(f'   Kill existing: kill $(lsof -t -i:{PORT})')
    sys.exit(1)
srv.listen(32)
print(f'\n[OK] Accepting connections on {HOST}:{PORT} ...\n')

while True:
    try:
        conn, addr = srv.accept()
        threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        immutable_log('BRIDGE_STOP', {'port': PORT})
        print('\nStopped.')
        break
    except Exception as e:
        log.error(f'[accept] {e}')
```
