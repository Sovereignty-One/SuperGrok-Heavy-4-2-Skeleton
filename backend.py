#!/usr/bin/env python3
"""
xAI Grok Terminal - Production Bridge
Port 9897 - Used by the official frontend
"""

import os
import time

import uvicorn
from blake3 import blake3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="xAI Grok Terminal",
    version="4.3.0-beta",
    description="Official xAI Production Bridge",
)


class ExecuteRequest(BaseModel):
    input: str
    hash: str
    session_id: str


@app.post("/codemaster/execute")
async def execute(req: ExecuteRequest):
    try:
        expected_hash = blake3((req.input + req.session_id).encode()).hexdigest()

        if expected_hash != req.hash:
            raise HTTPException(status_code=403, detail="Invalid payload hash")

        result = f" Processed: {req.input}"

        return {
            "status": "success",
            "result": result,
            "timestamp": time.time(),
            "session_id": req.session_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "xai-grok-terminal",
        "version": "4.3.0-beta",
        "port": 9897,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 9897))
    print(f"🚀 xAI Grok Terminal starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
