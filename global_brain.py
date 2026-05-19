from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import time
import os
import traceback

# === Sovereign Persistent Brain ===
from sovereign_persistent_brain.scripts.hydrate_brain import hydrate_brain
from sovereign_persistent_brain.scripts.persist_brain import persist_brain
from sovereign_persistent_brain.scripts.register_agent import register_agent
from sovereign_persistent_brain.scripts.dispatch_event import dispatch_event
from sovereign_persistent_brain.scripts.handle_error import handle_error
from sovereign_persistent_brain.scripts.self_sustain_loop import self_sustain_loop

app = FastAPI(title="XAI LiveTerminal + Sovereign Persistent Brain")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global brain state
brain_state = {"state": {}, "scarlog": []}

# ==================== REFACTORED ERROR HANDLING ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for clean error responses"""
    error_data = handle_error(exc, context=f"Global handler: {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": str(exc),
            "type": type(exc).__name__,
            "timestamp": time.time()
        }
    )

def safe_execute(func, *args, context: str = ""):
    """Decorator-style error wrapper"""
    try:
        return func(*args)
    except Exception as e:
        handle_error(e, context=context)
        raise

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    print("🧠 Initializing Sovereign Persistent Brain...")
    
    global brain_state
    brain_state = hydrate_brain()
    
    # Register LiveTerminal as an agent
    register_agent(
        agent_id="live-terminal",
        capabilities=["websocket", "voice", "command-processing", "pqc-signing"],
        metadata={"version": "1.0", "platform": "web"}
    )
    
    # Start self-sustaining background loop
    asyncio.create_task(self_sustain_loop())
    
    print("✅ Sovereign Brain fully initialized and running")

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 New client connected")

    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                # Try to parse as JSON
                message = json.loads(data)
                command = message.get("command", data)
            except json.JSONDecodeError:
                command = data

            # Dispatch event to brain + agents
            dispatch_event("user_command", {
                "command": command,
                "source": "live-terminal",
                "timestamp": time.time()
            })

            # Process command with error handling
            try:
                response = await process_command(command)
                await websocket.send_text(response)
            except Exception as e:
                error_msg = handle_error(e, context=f"process_command: {command}")
                await websocket.send_text(json.dumps({
                    "error": True,
                    "message": str(e),
                    "timestamp": time.time()
                }))

    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    except Exception as e:
        handle_error(e, context="websocket_endpoint")
        await websocket.close()

# ==================== PROCESS COMMAND ====================

async def process_command(command: str) -> str:
    """Main command processor with full brain integration"""
    command = command.strip()
    cmd_lower = command.lower()

    try:
        # === PQC Signing ===
        if cmd_lower.startswith("sign "):
            message = command[5:].strip()
            if not message:
                return "❌ Usage: sign <message>"

            from sovereign_persistent_brain.scripts.persist_brain import signer
            signature = signer.sign(message.encode())

            result = {
                "action": "sign",
                "message": message,
                "signature": signature.hex(),
                "algorithm": "ML-DSA-65",
                "timestamp": time.time()
            }

            persist_brain(brain_state["state"], new_logs=[{
                "type": "pqc_sign",
                "message": message[:60]
            }])

            return json.dumps(result, indent=2)

        # === PQC Verification ===
        elif cmd_lower.startswith("verify "):
            try:
                data = json.loads(command[7:].strip())
                signature = bytes.fromhex(data["signature"])
                message = data["message"].encode()
                public_key = bytes.fromhex(data["public_key"])

                from oqs import Signature
                verifier = Signature("ML-DSA-65")
                is_valid = verifier.verify(message, signature, public_key)

                return json.dumps({
                    "action": "verify",
                    "valid": is_valid,
                    "algorithm": "ML-DSA-65"
                }, indent=2)
            except Exception as e:
                return f"❌ Verification error: {str(e)}"

        # === Brain Status ===
        elif cmd_lower in ["status", "brain", "brain status"]:
            agents_file = "brain/agents.json"
            agent_count = 0
            if os.path.exists(agents_file):
                with open(agents_file) as f:
                    agent_count = len(json.load(f))

            return json.dumps({
                "brain_status": "Active",
                "pqc_algorithm": "ML-DSA-65",
                "scarlog_entries": len(brain_state["scarlog"]),
                "registered_agents": agent_count,
                "timestamp": time.time()
            }, indent=2)

        # === Key Rotation ===
        elif cmd_lower == "rotate keys":
            from sovereign_persistent_brain.scripts.rotate_keys import rotate_keys
            return json.dumps(rotate_keys(), indent=2)

        # === Token Rotation ===
        elif cmd_lower == "rotate tokens":
            from sovereign_persistent_brain.scripts.rotate_tokens import rotate_tokens
            return json.dumps(rotate_tokens(), indent=2)

        # === List Agents ===
        elif cmd_lower == "agents":
            agents_file = "brain/agents.json"
            if os.path.exists(agents_file):
                with open(agents_file) as f:
                    return json.dumps(json.load(f), indent=2)
            return "No agents registered."

        # === Dispatch Event ===
        elif cmd_lower.startswith("dispatch "):
            parts = command[9:].split(" ", 1)
            if len(parts) < 2:
                return "❌ Usage: dispatch <event_type> <json_data>"

            event_type = parts[0]
            try:
                data = json.loads(parts[1])
            except:
                data = {"raw": parts[1]}

            event = dispatch_event(event_type, data)
            return json.dumps(event, indent=2)

        # === Register Agent ===
        elif cmd_lower.startswith("register "):
            agent_id = command[9:].strip()
            if not agent_id:
                return "❌ Usage: register <agent_id>"
            register_agent(agent_id, capabilities=["websocket", "command"])
            return f"✅ Agent '{agent_id}' registered"

        # === Default ===
        else:
            return f"✅ Command received: {command}\n\nAvailable: sign, verify, status, rotate keys, agents, dispatch, register"

    except Exception as e:
        handle_error(e, context=f"process_command: {command}")
        return f"❌ Error: {str(e)}"

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "brain": "active",
        "pqc": "ML-DSA-65",
        "timestamp": time.time()
    }
