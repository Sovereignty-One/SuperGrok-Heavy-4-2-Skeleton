from concurrent.futures import ThreadPoolExecutor, as_completed
from engine.memory import MemoryStore


class WorkflowEngine:
    def __init__(self, agents, workflow_config):
        """
        agents: dict of agent_id -> Agent instance
        workflow_config: workflow section from YAML
        """
        self.agents = agents
        self.workflow = workflow_config

        # Persistent memory
        self.memory = MemoryStore()
        self.context = self.memory.load()

    def run(self):
        workflow_type = self.workflow.get("type")

        if workflow_type == "sequential":
            result = self._run_sequential()

        elif workflow_type == "parallel":
            result = self._run_parallel()

        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        # Save persistent memory after workflow execution
        self.memory.save(self.context)
        return result

    def _run_sequential(self):
        print("\n▶ Starting SEQUENTIAL workflow\n")

        for step in self.workflow.get("steps", []):
            agent_id = step["agent"]
            agent = self.agents[agent_id]

            print(f"→ Running agent: {agent_id}")
            output = agent.run(self.context)
            self.context[agent_id] = output

        print("\n✔ Sequential workflow completed\n")
        return self.context

    def _run_parallel(self):
        print("\n▶ Starting PARALLEL workflow\n")

        branches = self.workflow.get("branches", [])
        then_step = self.workflow.get("then", {})

        # Run branch agents in parallel
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.agents[agent_id].run, self.context): agent_id
                for agent_id in branches
            }

            for future in as_completed(futures):
                agent_id = futures[future]
                print(f"→ Parallel agent finished: {agent_id}")
                self.context[agent_id] = future.result()

        # Run final aggregation agent
        if then_step:
            final_agent_id = then_step["agent"]
            final_agent = self.agents[final_agent_id]

            print(f"\n→ Running aggregation agent: {final_agent_id}")
            output = final_agent.run(self.context)
            self.context[final_agent_id] = output

        print("\n✔ Parallel workflow completed\n")
        return self.context