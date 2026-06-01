"""Register an agent in the persistent brain store."""

from __future__ import annotations

from typing import Any

from ._brain_store import ensure_agents_file, load_brain, save_brain


def register_agent(agent_id: str, capabilities: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict:
    brain = load_brain()
    agents = [agent for agent in brain.get("agents", []) if agent.get("agent_id") != agent_id]
    record = {
        "agent_id": agent_id,
        "capabilities": capabilities or [],
        "metadata": metadata or {},
    }
    agents.append(record)
    brain["agents"] = agents
    ensure_agents_file(agents)
    save_brain(brain)
    return record
