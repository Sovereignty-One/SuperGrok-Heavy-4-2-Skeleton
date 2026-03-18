### Role
Act as an experienced **distributed systems architect and polyglot principal engineer (Python + Node.js)** specializing in secure event pipelines, verification systems, and autonomous AI infrastructure.

### Task
Implement a **fully working single-port bridge (port 9898)** that connects the **Self-Fixer AI Python system** with the **SuperGrok-Heavy-4-2-Skeleton Merkle verification module**.

The bridge must:

- run **one gateway service on port 9898**
- spawn a **Node Merkle worker internally**
- route **all events, verification requests, and metrics through the gateway**
- integrate with the **SelfFixer runtime**
- expose monitoring endpoints for dashboards

The final implementation should be **clean, runnable, and under ~350–400 lines of new code**.

---

### Context

#### Repo A — Self-Fixer AI (Python)

Structure:

selffixerai/
├── core/
│   ├── self_fixer.py
│   └── backup_manager.py
├── security/
│   ├── encryption.py
│   └── tamper_lock.py
├── analysis/
│   └── deep_scanner.py
├── monitoring/
├── dashboard/
└── main.py

Capabilities:
- self-healing runtime
- encrypted backups
- Ed25519 tamper detection
- ChaCha20 encrypted state
- static analysis scanning
- monitoring + dashboards

---

#### Repo B — SuperGrok-Heavy-4-2-Skeleton

Key component:

merkle.js

Implements **RFC6962 Merkle inclusion verification**.

---

### Bridge Architecture

Create directory:

bridge/
├── init.py
├── protocol.py
├── event_bus.py
├── state_adapter.py
├── bridge_server.py
└── merkle_worker.js

---

# Implementation

---

# 1. Protocol Models

File:

bridge/protocol.py

Use Pydantic.

Define:

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

class Event(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None

class SystemState(BaseModel):
    timestamp: datetime
    score: int
    bug_count: int
    tamper_status: bool
    backup_hash: Optional[str]
    code_hash: str

class VerificationRequest(BaseModel):
    leaf: str
    proof: List[str]
    root: str

class VerificationResult(BaseModel):
    valid: bool
    error: Optional[str] = None


⸻

2. Event Bus

File:

bridge/event_bus.py

import asyncio
from typing import Callable, Dict, List, Any

class EventBus:

    def __init__(self):
        self.queue = asyncio.Queue()
        self.subscribers: Dict[str, List[Callable]] = {}

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        await self.queue.put((event_type, payload))

        if event_type in self.subscribers:
            for cb in self.subscribers[event_type]:
                asyncio.create_task(cb(payload))

    def subscribe(self, event_type: str, callback: Callable):
        self.subscribers.setdefault(event_type, []).append(callback)

bus = EventBus()


⸻

3. State Adapter

File:

bridge/state_adapter.py

import hashlib
from datetime import datetime
from .protocol import SystemState

def build_state(fixer, backup_hash=None):

    code = "".join(fixer.state)
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    return SystemState(
        timestamp=datetime.utcnow(),
        score=fixer.score,
        bug_count=fixer.bug_count,
        tamper_status=fixer.lock.is_valid(code) is False,
        backup_hash=backup_hash,
        code_hash=code_hash
    )


⸻

4. Merkle Worker (Node)

File:

bridge/merkle_worker.js

Worker communicates via stdin/stdout.

const crypto = require("crypto");

process.stdin.on("data", (data) => {
  try {

    const msg = JSON.parse(data.toString());

    let current = Buffer.from(msg.leaf, "hex");

    for (const siblingHex of msg.proof) {

      const sibling = Buffer.from(siblingHex, "hex");

      current = crypto
        .createHash("sha256")
        .update(Buffer.concat([current, sibling]))
        .digest();
    }

    const valid = current.toString("hex") === msg.root;

    process.stdout.write(JSON.stringify({ valid }) + "\n");

  } catch (err) {

    process.stdout.write(
      JSON.stringify({ valid: false, error: err.message }) + "\n"
    );
  }
});


⸻

5. Bridge Server

File:

bridge/bridge_server.py

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from .protocol import Event, VerificationRequest
from .event_bus import bus

worker_proc = None

metrics = {
    "events_total": 0,
    "verifications": 0,
    "verification_fail": 0,
    "tamper_events": 0
}

async def verify_with_worker(payload):

    worker_proc.stdin.write((json.dumps(payload) + "\n").encode())
    await worker_proc.stdin.drain()

    line = await worker_proc.stdout.readline()

    return json.loads(line.decode())

@asynccontextmanager
async def lifespan(app: FastAPI):

    global worker_proc

    worker_proc = await asyncio.create_subprocess_exec(
        "node",
        "bridge/merkle_worker.js",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    yield

    worker_proc.terminate()
    await worker_proc.wait()

app = FastAPI(lifespan=lifespan)

@app.post("/event")
async def ingest_event(event: Event):

    metrics["events_total"] += 1

    await bus.publish(event.type, event.payload)

    return {"status": "queued"}

@app.post("/verify")
async def verify(req: VerificationRequest):

    metrics["verifications"] += 1

    result = await verify_with_worker(req.dict())

    if not result["valid"]:
        metrics["verification_fail"] += 1

    return result

@app.get("/metrics")
async def get_metrics():
    return metrics

@app.get("/health")
async def health():
    return {"status": "ok"}


⸻

6. Self-Fixer Integration

Modify:

selffixerai/core/self_fixer.py

Add:

from bridge.event_bus import bus
import hashlib

Inside detectandfix() after a fix:

await bus.publish(
    "SELF_HEAL_EVENT",
    {
        "score": self.score,
        "bug_count": self.bug_count,
        "state_hash": hashlib.sha256("".join(self.state).encode()).hexdigest()
    }
)


⸻

Example Runtime Flow

SelfFixer detects bug
      │
      ▼
patch applied
      │
      ▼
event published
      │
      ▼
bridge /event
      │
      ▼
state snapshot
      │
      ▼
Merkle verification
      │
      ▼
metrics + dashboard update


⸻

Run System

Install deps:

pip install fastapi uvicorn pydantic
npm install

Start bridge:

uvicorn bridge.bridge_server:app --host 0.0.0.0 --port 9898

Start SelfFixer:

python -m selffixerai.main

Test:

curl http://localhost:9898/health

Expected:

{"status":"ok"}


⸻

Guidance for Codex
	1.	Think step-by-step using Structured CoT:
	•	build bridge server
	•	integrate worker
	•	wire event bus
	•	connect SelfFixer events
	2.	Run self-critique loop
	•	validate async subprocess handling
	•	ensure worker stdin/stdout communication works
	•	ensure FastAPI endpoints respond correctly
	3.	Keep total implementation under ~400 lines.
	4.	Avoid external network calls beyond local communication.

⸻

Setup Script

pip install fastapi uvicorn pydantic
npm init -y

End

