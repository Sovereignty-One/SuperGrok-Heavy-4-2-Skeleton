import yaml


def load_config(path):
    """
    Load and validate YAML configuration file.
    Returns parsed config as a dictionary.
    """
    with open(path, "r") as file:
        config = yaml.safe_load(file)

    validate_config(config)
    return config


def validate_config(config):
    # Basic top-level validation
    if "agents" not in config:
        raise ValueError("Config must define 'agents'")

    if "workflow" not in config:
        raise ValueError("Config must define 'workflow'")

    # Validate agents
    agent_ids = set()
    for agent in config["agents"]:
        if "id" not in agent or "role" not in agent or "goal" not in agent:
            raise ValueError("Each agent must have id, role, and goal")

        if agent["id"] in agent_ids:
            raise ValueError(f"Duplicate agent id found: {agent['id']}")

        agent_ids.add(agent["id"])

    # Validate workflow
    workflow = config["workflow"]
    workflow_type = workflow.get("type")

    if workflow_type not in ("sequential", "parallel"):
        raise ValueError("workflow.type must be 'sequential' or 'parallel'")

    if workflow_type == "sequential":
        if "steps" not in workflow:
            raise ValueError("Sequential workflow must define 'steps'")

        for step in workflow["steps"]:
            if step.get("agent") not in agent_ids:
                raise ValueError(f"Unknown agent in steps: {step.get('agent')}")

    if workflow_type == "parallel":
        if "branches" not in workflow:
            raise ValueError("Parallel workflow must define 'branches'")

        for agent_id in workflow["branches"]:
            if agent_id not in agent_ids:
                raise ValueError(f"Unknown agent in branches: {agent_id}")

        if "then" in workflow:
            if workflow["then"].get("agent") not in agent_ids:
                raise ValueError(
                    f"Unknown agent in then: {workflow['then'].get('agent')}"
                )