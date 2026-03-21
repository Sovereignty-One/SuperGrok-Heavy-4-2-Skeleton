---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description:
---

# Chain of Command GPT Grok Claude GitHub-copilot
#!/usr/bin/env python3

SuperGrok Unified Bridge v4.0
Single port 9898 — HTTP + WebSocket upgrade on same socket.
No external dependencies. Pure Python 3.6+ stdlib only.

Quick start (a-Shell or iSH):
export ANTHROPIC_API_KEY=sk-ant-…
python3 bridge.py

Then open Safari at:  http://127.0.0.1:9898


import os, sys, json, socket, hashlib, base64, threading, subprocess
import urllib.request, urllib.error, time
from pathlib import Path

PORT = int(os.environ.get(‘SG_PORT’, 9898))
HOST = ‘127.0.0.1’
KEYS = {
‘anthropic’: os.environ.get(‘ANTHROPIC_API_KEY’, ‘’),
‘openai’:    os.environ.get(‘OPENAI_API_KEY’, ‘’),
‘grok’:      os.environ.get(‘GROK_API_KEY’, os.environ.get(‘XAI_API_KEY’, ‘’)),
}

# —————————————————————————

# HTML discovery

# —————————————————————————

def find_html():
dirs = [Path.home(), Path.cwd(), Path(’/root’), Path(’/var/mobile’)]
pats = [‘SuperGrok_v107*’, ‘SuperGrok_v10*’, ‘SuperGrok*.html’, ‘*.html’]
for d in dirs:
for p in pats:
hits = sorted(d.glob(p), reverse=True)
if hits:
return str(hits[0])
return None

HTML_FILE = find_html()

# —————————————————————————

# AI providers

# —————————————————————————

def post_json(url, headers, body):
try:
data = json.dumps(body).encode()
req  = urllib.request.Request(url, data=data, headers=headers, method=‘POST’)
with urllib.request.urlopen(req, timeout=60) as r:
return json.loads(r.read()), None
except urllib.error.HTTPError as e:
return None, ‘%d: %s’ % (e.code, e.read().decode()[:200])
except Exception as e:
return None, str(e)

def ai_claude(messages, model=‘claude-opus-4-5’):
k = KEYS[‘anthropic’]
if not k: return None, ‘ANTHROPIC_API_KEY not set’
r, e = post_json(
‘https://api.anthropic.com/v1/messages’,
{‘Content-Type’: ‘application/json’, ‘x-api-key’: k, ‘anthropic-version’: ‘2023-06-01’},
{‘model’: model, ‘max_tokens’: 2000, ‘messages’: messages}
)
return (r[‘content’][0][‘text’], None) if r else (None, e)

def ai_openai(messages, model=‘gpt-4o’):
k = KEYS[‘openai’]
if not k: return None, ‘OPENAI_API_KEY not set’
r, e = post_json(
‘https://api.openai.com/v1/chat/completions’,
{‘Content-Type’: ‘application/json’, ‘Authorization’: ’Bearer ’ + k},
{‘model’: model, ‘max_tokens’: 2000, ‘messages’: messages}
)
return (r[‘choices’][0][‘message’][‘content’], None) if r else (None, e)

def ai_grok(messages, model=‘grok-3-latest’):
k = KEYS[‘grok’]
if not k: return None, ‘GROK_API_KEY not set’
r, e = post_json(
‘https://api.x.ai/v1/chat/completions’,
{‘Content-Type’: ‘application/json’, ‘Authorization’: ’Bearer ’ + k},
{‘model’: model, ‘max_tokens’: 2000, ‘messages’: messages}
)
return (r[‘choices’][0][‘message’][‘content’], None) if r else (None, e)

def route_ai(agent, messages, model=None):
a = (agent or ‘claude’).lower()
if   a in (‘claude’,‘anthropic’,‘arbiter’): order = [ai_claude, ai_openai, ai_grok]
elif ‘gpt’    in a or ‘openai’   in a:  order = [ai_openai, ai_claude, ai_grok]
elif ‘grok’   in a or ‘xai’      in a:  order = [ai_grok,   ai_claude, ai_openai]
else:                                    order = [ai_claude, ai_openai, ai_grok]
for fn in order:
text, err = fn(messages, model) if model else fn(messages)
if text: return text, None
return None, ‘All providers failed or no API keys set’

def shell_exec(cmd):
try:
r = subprocess.run(cmd, shell=True, capture_output=True,
text=True, timeout=30, cwd=str(Path.home()))
return (r.stdout + r.stderr)[:8192]
except subprocess.TimeoutExpired:
return ‘Timed out (30s)’
except Exception as e:
return str(e)

# —————————————————————————

# WebSocket RFC 6455 — raw implementation, no library needed

# —————————————————————————

WS_GUID = ‘258EAFA5-E914-47DA-95CA-C5AB0DC85B11’

def ws_accept_key(key):
raw = hashlib.sha1((key.strip() + WS_GUID).encode()).digest()
return base64.b64encode(raw).decode()

def ws_handshake(conn, key):
resp = (
‘HTTP/1.1 101 Switching Protocols\r\n’
‘Upgrade: websocket\r\n’
‘Connection: Upgrade\r\n’
’Sec-WebSocket-Accept: ’ + ws_accept_key(key) + ‘\r\n’
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

-
try:
    h = recv_exact(2)
    opcode = h[0] & 0x0F
    masked = bool(h[1] & 0x80)
    plen   = h[1] & 0x7F
    if   plen == 126: plen = int.from_bytes(recv_exact(2), 'big')
    elif plen == 127: plen = int.from_bytes(recv_exact(8), 'big')
    mask = recv_exact(4) if masked else b'\x00\x00\x00\x00'
    data = bytearray(recv_exact(plen))
    if masked:
        for i in range(len(data)):
            data[i] ^= mask[i % 4]
    return opcode, bytes(data)
except Exception:
    return None, None


def ws_write(conn, payload, opcode=0x01):
if isinstance(payload, str):
payload = payload.encode()
n = len(payload)
if   n < 126:    hdr = bytes([0x80 | opcode, n])
elif n < 65536:  hdr = bytes([0x80 | opcode, 126]) + n.to_bytes(2, ‘big’)
else:            hdr = bytes([0x80 | opcode, 127]) + n.to_bytes(8, ‘big’)
try:
conn.sendall(hdr + payload)
return True
except Exception:
return False

def ws_json(conn, obj):
return ws_write(conn, json.dumps(obj))

# —————————————————————————

# WebSocket message handler

# —————————————————————————

def handle_ws_msg(conn, raw):
try:
msg = json.loads(raw)
except Exception:
ws_json(conn, {‘type’: ‘error’, ‘error’: ‘invalid JSON’})
return
t   = msg.get(‘type’, ‘’)
rid = msg.get(‘request_id’, ‘’)
print(’  [WS] %s’ % t)

-
if t == 'ping':
    ws_json(conn, {'type': 'pong', 'ts': int(time.time() * 1000)})

elif t in ('agent_query', 'ai_query', 'chat', 'message', 'query'):
    agent    = msg.get('agent', msg.get('provider', 'claude'))
    prompt   = msg.get('prompt', msg.get('message', msg.get('content', '')))
    history  = msg.get('history', [])
    messages = history + [{'role': 'user', 'content': prompt}]
    ws_json(conn, {'type': 'agent_thinking', 'agent': agent, 'request_id': rid})
    text, err = route_ai(agent, messages, msg.get('model'))
    ws_json(conn, {
        'type': 'agent_response', 'agent': agent, 'request_id': rid,
        'text': text or '', 'response': text or '', 'error': err,
    })

elif t in ('exec', 'shell_exec', 'terminal', 'run'):
    cmd = msg.get('cmd', msg.get('command', ''))
    ws_json(conn, {'type': 'exec_result', 'output': shell_exec(cmd), 'cmd': cmd})

elif t in ('ssh_input', 'ssh_data'):
    ws_json(conn, {'type': 'ssh_data', 'data': shell_exec(msg.get('data', '').strip())})

elif t == 'ssh_connect':
    ws_json(conn, {
        'type': 'ssh_connected',
        'banner': 'SuperGrok SSH Bridge\n%s:%s\n' % (msg.get('host', 'localhost'), msg.get('port', 22)),
        'prompt': '%s@%s:~$ ' % (msg.get('username', 'root'), msg.get('host', 'localhost')),
    })

elif t == 'tts_xai':
    text = msg.get('text', '')
    key  = msg.get('key', KEYS.get('grok',''))
    # xAI TTS endpoint (when available)
    if key:
        try:
            r, err = post_json(
                'https://api.x.ai/v1/audio/speech',
                {'Content-Type':'application/json','Authorization':'Bearer '+key},
                {'model':'tts-1','input':text,'voice':msg.get('voice','shimmer')}
            )
            if r:
                ws_json(conn, {'type':'tts_result','text':text,'status':'ok'})
                # Fall through to local TTS as well
            else:
                threading.Thread(target=lambda: subprocess.run(
                    'say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text,text), shell=True
                ), daemon=True).start()
                ws_json(conn, {'type':'speak_result','text':text})
        except Exception:
            ws_json(conn, {'type':'speak_result','text':text})
    else:
        threading.Thread(target=lambda: subprocess.run(
            'say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text,text), shell=True
        ), daemon=True).start()
        ws_json(conn, {'type':'speak_result','text':text})

elif t == 'speak':
    text = msg.get('text', '')
    threading.Thread(
        target=lambda: subprocess.run(
            'say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text, text),
            shell=True
        ), daemon=True
    ).start()
    ws_json(conn, {'type': 'speak_result', 'text': text})

elif t == 'stt_start':
    ws_json(conn, {'type': 'stt_ready'})

elif t == 'keys_set':
    for k, v in (msg.get('keys') or {}).items():
        if k in KEYS and v:
            KEYS[k] = v
            os.environ[k.upper() + '_API_KEY'] = v
    ws_json(conn, {'type': 'keys_saved'})

elif t == 'health':
    ws_json(conn, {
        'type': 'health_ok', 'version': 'v4.0',
        'keys': {k: bool(v) for k, v in KEYS.items()},
    })

else:
    ws_json(conn, {'type': 'ack', 'received': t, 'ts': int(time.time() * 1000)})


def run_ws(conn, addr, path):
print(’[WS]  + %s  path=%s’ % (str(addr), path))
ws_json(conn, {
‘type’: ‘connected’, ‘version’: ‘SuperGrok Bridge v4.0’,
‘keys’: {k: bool(v) for k, v in KEYS.items()},
})
try:
while True:
opcode, payload = ws_read_frame(conn)
if opcode is None: break
if opcode == 0x8:  break
if opcode == 0x9:  ws_write(conn, b’’, 0xA); continue
if opcode in (0x1, 0x2): handle_ws_msg(conn, payload)
except Exception as e:
print(’[WS]  ! %s  %s’ % (str(addr), e))
finally:
print(’[WS]  - %s’ % str(addr))
try: conn.close()
except: pass

# —————————————————————————

# HTTP handler

# —————————————————————————

CORS_HDR = (
‘Access-Control-Allow-Origin: *\r\n’
‘Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n’
‘Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key\r\n’
)

def http_send(conn, code, body, ctype=‘application/json’):
phrase = {200: ‘OK’, 204: ‘No Content’, 404: ‘Not Found’, 405: ‘Method Not Allowed’}.get(code, ‘OK’)
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

def handle_http(conn, method, path, body_bytes):
if method == ‘OPTIONS’:
http_send(conn, 204, b’’)
return

-
if method == 'GET':
    if path in ('/', '/index.html'):
        if HTML_FILE and Path(HTML_FILE).exists():
            http_send(conn, 200, Path(HTML_FILE).read_bytes(), 'text/html')
        else:
            http_send(conn, 200, fallback_html(), 'text/html')

    elif path == '/api/tls/generate':
        # Generate self-signed TLS certificate
        import subprocess, time
        days = body.get('days', 30)
        cn   = body.get('cn', 'supergrok.local')
        key_f = str(Path.home() / f'sg-tls-{int(time.time())}.key')
        crt_f = str(Path.home() / f'sg-tls-{int(time.time())}.crt')
        result = subprocess.run(
            f'openssl req -x509 -nodes -newkey ec -pkeyopt ec_paramgen_curve:P-256 '
            f'-keyout "{key_f}" -out "{crt_f}" -days {days} -subj "/CN={cn}" 2>&1',
            shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            import hashlib
            with open(crt_f, 'rb') as fh:
                fp = hashlib.sha256(fh.read()).hexdigest()[:16]
            meta = {'cert': crt_f, 'key': key_f, 'cn': cn, 'days': days, 'fingerprint': fp}
            open(str(Path.home() / 'sg_tls_cert.json'), 'w').write(json.dumps(meta))
            http_send(conn, 200, meta)
        else:
            http_send(conn, 500, {'error': result.stdout + result.stderr})

    elif path == '/api/tls/rotate':
        # Rotate cert — same as generate
        body['path'] = '/api/tls/generate'
        handle_http(conn, 'POST', '/api/tls/generate', json.dumps(body).encode())
        return

    elif path == '/api/tls/status':
        cert_json = Path.home() / 'sg_tls_cert.json'
        if cert_json.exists():
            http_send(conn, 200, json.loads(cert_json.read_text()))
        else:
            http_send(conn, 200, {'status': 'no cert', 'hint': 'POST /api/tls/generate'})

    elif path == '/api/sinkhole':
        # Write domain sinkhole entries to /etc/hosts or local file
        domains = body.get('domains', [])
        ip      = body.get('ip', '127.0.0.1')
        lines   = []
        for d in domains:
            lines.append(f'{ip} {d}')
        # Try /etc/hosts (requires sudo), fall back to log
        sinkhole_file = Path.home() / 'sg_sinkhole.hosts'
        with open(sinkhole_file, 'a') as fh:
            fh.write('\n'.join(lines) + '\n')
        # Attempt system hosts update
        result = subprocess.run(
            f'echo "\n'.join(lines) + '" | sudo tee -a /etc/hosts',
            shell=True, capture_output=True, text=True, timeout=10
        ) if hasattr(subprocess, 'run') else None
        http_send(conn, 200, {'count': len(domains), 'file': str(sinkhole_file)})

    elif path == '/api/firewall/block':
        # Block IP using ufw or log entry
        ip  = body.get('ip', '')
        dur = body.get('duration', 300)
        if ip:
            subprocess.run(f'sudo ufw deny from {ip} to any port 9898 2>/dev/null', shell=True, timeout=10)
            # Schedule unblock
            def unblock(ip, dur):
                import time
                time.sleep(dur)
                subprocess.run(f'sudo ufw delete deny from {ip} to any port 9898 2>/dev/null', shell=True)
            threading.Thread(target=unblock, args=(ip, dur), daemon=True).start()
        http_send(conn, 200, {'blocked': ip, 'duration': dur})

    elif path == '/api/enforce':
        # Signal-safe enforcement actions (no process killing — just logging + reporting)
        subjects = body.get('subjects', [])
        results  = {}
        for s in subjects:
            results[s] = 'enforced'
        http_send(conn, 200, {'enforced': len(subjects), 'results': results})

    elif path.startswith('/auth/keycloak'):
        # Sovereign OAuth — Keycloak proxy
        if path == '/auth/keycloak/test':
            r, e = post_json('http://127.0.0.1:8443/realms/master/.well-known/openid-configuration', {}, {})
            if r: http_send(conn, 200, {'keycloak': 'ok', 'issuer': r.get('issuer','')})
            else:  http_send(conn, 200, {'keycloak': 'offline', 'note': 'Start Keycloak on :8443'})
        else:
            http_send(conn, 404, {'error': 'Keycloak endpoint: ' + path})

    elif path == '/api/health':
        http_send(conn, 200, {
            'status': 'ok', 'version': 'v4.0', 'port': PORT,
            'html': HTML_FILE or 'not found',
            'keys': {k: bool(v) for k, v in KEYS.items()},
            'ts': int(time.time()),
        })

    elif path.startswith('/oauth') or path.startswith('/.well-known'):
        import hashlib, base64, secrets, time as _time
        sub_path = path.replace('/oauth','',1)
-
        if path == '/.well-known/openid-configuration' or sub_path == '/.well-known/openid-configuration':
            issuer = 'http://127.0.0.1:%d/oauth' % PORT
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
-
        elif sub_path == '/.well-known/jwks.json' or path == '/.well-known/jwks.json':
            http_send(conn, 200, {'keys': [{'kty':'oct','alg':'HS256','use':'sig','kid':'sg-key-1'}]})
-
        elif method == 'POST' and sub_path == '/token':
            grant = body.get('grant_type','')
            now   = int(_time.time())
            token = secrets.token_urlsafe(32)
            jwt_claims = {
                'iss': 'http://127.0.0.1:%d/oauth' % PORT,
                'sub': body.get('client_id','sg_user'),
                'iat': now, 'exp': now+3600,
                'jti': secrets.token_hex(8),
                'scope': body.get('scope','openid profile'),
            }
            http_send(conn, 200, {
                'access_token': token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'scope': jwt_claims['scope'],
                'claims': jwt_claims,
            })
-
        elif method == 'POST' and sub_path == '/introspect':
            t = body.get('token','')
            http_send(conn, 200, {'active': bool(t), 'token': t[:8]+'...' if t else None})
-
        elif method == 'POST' and sub_path == '/revoke':
            http_send(conn, 200, {'revoked': True, 'token': body.get('token','')[:8]+'...'})
-
        else:
            http_send(conn, 200, {'ok': True, 'path': path, 'note': 'OAuth endpoint'})


    elif path.startswith('/oauth') or path.startswith('/.well-known'):
        import hashlib, base64, secrets, time as _time
        sub_path = path.replace('/oauth','',1)
-
        if path == '/.well-known/openid-configuration' or sub_path == '/.well-known/openid-configuration':
            issuer = 'http://127.0.0.1:%d/oauth' % PORT
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
-
        elif sub_path == '/.well-known/jwks.json' or path == '/.well-known/jwks.json':
            http_send(conn, 200, {'keys': [{'kty':'oct','alg':'HS256','use':'sig','kid':'sg-key-1'}]})
-
        elif method == 'POST' and sub_path == '/token':
            grant = body.get('grant_type','')
            now   = int(_time.time())
            token = secrets.token_urlsafe(32)
            jwt_claims = {
                'iss': 'http://127.0.0.1:%d/oauth' % PORT,
                'sub': body.get('client_id','sg_user'),
                'iat': now, 'exp': now+3600,
                'jti': secrets.token_hex(8),
                'scope': body.get('scope','openid profile'),
            }
            http_send(conn, 200, {
                'access_token': token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'scope': jwt_claims['scope'],
                'claims': jwt_claims,
            })
-
        elif method == 'POST' and sub_path == '/introspect':
            t = body.get('token','')
            http_send(conn, 200, {'active': bool(t), 'token': t[:8]+'...' if t else None})
-
        elif method == 'POST' and sub_path == '/revoke':
            http_send(conn, 200, {'revoked': True, 'token': body.get('token','')[:8]+'...'})
-
        else:
            http_send(conn, 200, {'ok': True, 'path': path, 'note': 'OAuth endpoint'})

    else:
        http_send(conn, 404, {'error': 'not found'})

elif method == 'POST':
    body = {}
    if body_bytes:
        try: body = json.loads(body_bytes)
        except: pass
   - -    
    if path in ('/api/ai', '/api/agent', '/api/chat'):
        agent    = body.get('agent', 'claude')
        prompt   = body.get('prompt', body.get('message', body.get('content', '')))
        history  = body.get('history', [])
        messages = history + [{'role': 'user', 'content': prompt}]
        text, err = route_ai(agent, messages, body.get('model'))
        http_send(conn, 200, {
            'type': 'agent_response', 'agent': agent,
            'text': text or '', 'response': text or '', 'error': err,
        })
-
    elif path in ('/api/exec', '/api/terminal', '/api/shell'):
        cmd = body.get('cmd', body.get('command', ''))
        http_send(conn, 200, {'type': 'exec_result', 'output': shell_exec(cmd)})

    elif path == '/api/keys':
        for k, v in body.items():
            if k in KEYS and v:
                KEYS[k] = v
                os.environ[k.upper() + '_API_KEY'] = v
        http_send(conn, 200, {'saved': True, 'keys': {k: bool(v) for k, v in KEYS.items()}})

    elif path == '/api/speak':
        text = body.get('text', '')
        subprocess.run('say "%s" 2>/dev/null || espeak "%s" 2>/dev/null' % (text, text), shell=True)
        http_send(conn, 200, {'done': True})

    else:
        http_send(conn, 404, {'error': 'not found'})


def fallback_html():
rows = ‘’
for k, v in KEYS.items():
color = ‘#3fb950’ if v else ‘#ff6b6b’
note  = ‘set’ if v else (‘not set – export %s_API_KEY=…’ % k.upper())
rows += ‘<li style="color:%s">%s: %s</li>’ % (color, k, note)
return (
‘<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SuperGrok Bridge</title>’
‘<style>body{background:#0d1117;color:#c9d1d9;font-family:monospace;padding:40px;’
‘max-width:700px;margin:0 auto}h1{color:#00ffc8}’
‘code{background:#161b22;padding:2px 6px;border-radius:4px;color:#79c0ff}’
‘a{color:#58a6ff}</style></head><body>’
‘<h1>SuperGrok Bridge v4.0 — Running</h1>’
‘<p style="color:#3fb950">HTTP + WebSocket on port %d</p>’
‘<p style="color:#ff9800">Place SuperGrok_v107_FINAL.html in ~/ then reload.</p>’
‘<ul>%s</ul>’
‘<p><a href="/api/health">/api/health</a></p>’
‘</body></html>’
) % (PORT, rows)
return html.encode()

# —————————————————————————

# Connection dispatcher — same socket serves HTTP and WS

# —————————————————————————

def handle_conn(conn, addr):
conn.settimeout(30)
try:
buf = b’’
while b’\r\n\r\n’ not in buf:
c = conn.recv(4096)
if not c: return
buf += c
if len(buf) > 65536: return

-
    head_raw, _, body_start = buf.partition(b'\r\n\r\n')
    lines    = head_raw.decode('utf-8', errors='replace').split('\r\n')
    req      = lines[0].split()
    if len(req) < 2: return
    method   = req[0].upper()
    path     = req[1]

    hdrs = {}
    for ln in lines[1:]:
        if ':' in ln:
            k, _, v = ln.partition(':')
            hdrs[k.strip().lower()] = v.strip()

    # WebSocket upgrade path
    if hdrs.get('upgrade', '').lower() == 'websocket' and 'sec-websocket-key' in hdrs:
        ws_handshake(conn, hdrs['sec-websocket-key'])
        conn.settimeout(None)
        run_ws(conn, addr, path)
        return

    # Regular HTTP
    clen     = int(hdrs.get('content-length', 0))
    body_raw = body_start
    while len(body_raw) < clen:
        c = conn.recv(min(4096, clen - len(body_raw)))
        if not c: break
        body_raw += c

    handle_http(conn, method, path, body_raw)

except Exception as e:
    pass
finally:
    try: conn.close()
    except: pass


# —————————————————————————

# Entry point

# —————————————————————————

if **name** == ‘**main**’:
print(’=’ * 58)
print(’  SuperGrok Unified Bridge v4.0’)
print(’  HTTP + WebSocket on single port %d — no split’ % PORT)
print(’=’ * 58)
print(’  Dashboard : http://127.0.0.1:%d’ % PORT)
print(’  Health    : http://127.0.0.1:%d/api/health’ % PORT)
print(’  HTML      : %s’ % (HTML_FILE or ‘NOT FOUND — place SuperGrok_v107_FINAL.html in ~/’))
print()
print(’  Claude    : %s’ % (‘ready’ if KEYS[‘anthropic’] else ‘export ANTHROPIC_API_KEY=sk-ant-…’))
print(’  OpenAI    : %s’ % (‘ready’ if KEYS[‘openai’]    else ‘export OPENAI_API_KEY=sk-…’))
print(’  Grok      : %s’ % (‘ready’ if KEYS[‘grok’]      else ‘export GROK_API_KEY=xai-…’))
print()
print(’  OPEN SAFARI AT: http://127.0.0.1:9898’)
print(’=’ * 58)


srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    srv.bind((HOST, PORT))
except OSError as e:
    print('\nCannot bind %s:%d — %s' % (HOST, PORT, e))
    print('Kill the existing process: kill $(lsof -t -i:%d)' % PORT)
    sys.exit(1)
srv.listen(32)
print('\n[OK]  Accepting connections\n')
while True:
    try:
        conn, addr = srv.accept()
        threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print('\nStopped.')
        break
    except Exception as e:
        print('[ERR] %s' % e)
Describe what your agent does here.
