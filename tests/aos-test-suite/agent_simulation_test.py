#!/usr/bin/env python3
"""
AOS Agent Simulation Test
Simulates synthetic agents performing real workflows.
"""

import os
import time
import uuid
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import argparse

API_BASE = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AOS_API_KEY", "test")


class AgentType(Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"


class SkillType(Enum):
    HTTP_CALL = "http_call"
    LLM_INVOKE = "llm_invoke"
    JSON_TRANSFORM = "json_transform"
    FS_READ = "fs_read"
    FS_WRITE = "fs_write"
    WEBHOOK_SEND = "webhook_send"
    EMAIL_SEND = "email_send"


@dataclass
class SyntheticAgent:
    id: str
    name: str
    agent_type: AgentType
    capabilities: List[SkillType]
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_cost_cents: int = 0


@dataclass
class WorkflowStep:
    skill: SkillType
    params: Dict[str, Any]
    expected_cost_cents: int = 0


@dataclass
class Workflow:
    name: str
    steps: List[WorkflowStep]
    expected_duration_ms: int = 0


class AgentSimulator:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agents: List[SyntheticAgent] = []
        self.workflows: List[Workflow] = []

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def _request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        json_data: Optional[Dict] = None,
    ) -> Dict:
        url = f"{self.base_url}{path}"
        async with session.request(
            method,
            url,
            headers=self._headers(),
            json=json_data,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            return await resp.json()

    # ==================== AGENT CREATION ====================

    def create_synthetic_agents(self, count: int = 10) -> List[SyntheticAgent]:
        """Create synthetic agents for simulation"""
        print(f"\n🤖 Creating {count} synthetic agents...")

        for i in range(count):
            agent_type = AgentType.ORCHESTRATOR if i < count // 5 else AgentType.WORKER

            if agent_type == AgentType.ORCHESTRATOR:
                capabilities = list(SkillType)  # All skills
            else:
                # Workers get random subset
                import random

                capabilities = random.sample(list(SkillType), k=random.randint(2, 5))

            agent = SyntheticAgent(
                id=f"agent-{uuid.uuid4().hex[:8]}",
                name=f"SyntheticAgent-{i+1}",
                agent_type=agent_type,
                capabilities=capabilities,
            )
            self.agents.append(agent)
            print(
                f"  Created: {agent.name} ({agent.agent_type.value}) - {len(capabilities)} skills"
            )

        return self.agents

    # ==================== WORKFLOW DEFINITIONS ====================

    def create_test_workflows(self) -> List[Workflow]:
        """Create test workflows"""
        print("\n📋 Creating test workflows...")

        self.workflows = [
            # Workflow 1: Simple data fetch
            Workflow(
                name="DataFetch",
                steps=[
                    WorkflowStep(
                        SkillType.HTTP_CALL, {"url": "https://api.example.com/data"}, 0
                    ),
                    WorkflowStep(SkillType.JSON_TRANSFORM, {"jq": ".results"}, 0),
                ],
                expected_duration_ms=600,
            ),
            # Workflow 2: LLM Analysis
            Workflow(
                name="LLMAnalysis",
                steps=[
                    WorkflowStep(
                        SkillType.LLM_INVOKE,
                        {"prompt": "Analyze data", "model": "claude-3-sonnet"},
                        5,
                    ),
                ],
                expected_duration_ms=2000,
            ),
            # Workflow 3: Full pipeline
            Workflow(
                name="FullPipeline",
                steps=[
                    WorkflowStep(
                        SkillType.HTTP_CALL, {"url": "https://api.example.com"}, 0
                    ),
                    WorkflowStep(SkillType.JSON_TRANSFORM, {"jq": "."}, 0),
                    WorkflowStep(SkillType.LLM_INVOKE, {"prompt": "Process"}, 5),
                    WorkflowStep(
                        SkillType.WEBHOOK_SEND, {"url": "https://webhook.site/test"}, 0
                    ),
                ],
                expected_duration_ms=3000,
            ),
            # Workflow 4: Heavy compute
            Workflow(
                name="HeavyCompute",
                steps=[
                    WorkflowStep(SkillType.LLM_INVOKE, {"prompt": "Step 1"}, 5),
                    WorkflowStep(SkillType.LLM_INVOKE, {"prompt": "Step 2"}, 5),
                    WorkflowStep(SkillType.LLM_INVOKE, {"prompt": "Step 3"}, 5),
                ],
                expected_duration_ms=6000,
            ),
            # Workflow 5: File operations
            Workflow(
                name="FileOps",
                steps=[
                    WorkflowStep(SkillType.FS_READ, {"path": "/tmp/input.json"}, 0),
                    WorkflowStep(SkillType.JSON_TRANSFORM, {"jq": ".data"}, 0),
                    WorkflowStep(SkillType.FS_WRITE, {"path": "/tmp/output.json"}, 0),
                ],
                expected_duration_ms=200,
            ),
        ]

        for wf in self.workflows:
            total_cost = sum(s.expected_cost_cents for s in wf.steps)
            print(
                f"  {wf.name}: {len(wf.steps)} steps, ~{total_cost}¢, ~{wf.expected_duration_ms}ms"
            )

        return self.workflows

    # ==================== SIMULATION ====================

    async def simulate_workflow(
        self, session: aiohttp.ClientSession, agent: SyntheticAgent, workflow: Workflow
    ) -> Dict:
        """Simulate a single workflow execution"""
        plan = [
            {"skill": step.skill.value, "params": step.params}
            for step in workflow.steps
        ]

        start = time.perf_counter()
        try:
            result = await self._request(
                session,
                "POST",
                "/api/v1/runtime/simulate",
                {"plan": plan, "budget_cents": 1000, "agent_id": agent.id},
            )
            duration_ms = (time.perf_counter() - start) * 1000

            if result.get("feasible"):
                agent.jobs_completed += 1
                agent.total_cost_cents += result.get("estimated_cost_cents", 0)
                return {
                    "success": True,
                    "workflow": workflow.name,
                    "agent": agent.name,
                    "cost_cents": result.get("estimated_cost_cents", 0),
                    "duration_ms": duration_ms,
                    "feasible": True,
                }
            else:
                agent.jobs_failed += 1
                return {
                    "success": False,
                    "workflow": workflow.name,
                    "agent": agent.name,
                    "reason": "not_feasible",
                    "risks": result.get("risks", []),
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            agent.jobs_failed += 1
            return {
                "success": False,
                "workflow": workflow.name,
                "agent": agent.name,
                "reason": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    async def run_simulation(
        self, num_workflows: int = 100, concurrency: int = 10
    ) -> Dict:
        """Run full agent simulation"""
        print(
            f"\n🚀 Running simulation: {num_workflows} workflows, {concurrency} concurrent"
        )

        import random

        results = []
        start = time.perf_counter()

        async with aiohttp.ClientSession() as session:
            sem = asyncio.Semaphore(concurrency)

            async def run_one():
                async with sem:
                    agent = random.choice(self.agents)
                    workflow = random.choice(self.workflows)
                    return await self.simulate_workflow(session, agent, workflow)

            tasks = [run_one() for _ in range(num_workflows)]
            results = await asyncio.gather(*tasks)

        duration = time.perf_counter() - start

        # Aggregate results
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        total_cost = sum(r.get("cost_cents", 0) for r in successful)
        latencies = [r.get("duration_ms", 0) for r in results]

        return {
            "total_workflows": num_workflows,
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": f"{len(successful)/num_workflows*100:.1f}%",
            "total_cost_cents": total_cost,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "duration_seconds": duration,
            "workflows_per_second": num_workflows / duration,
            "agent_stats": [
                {
                    "name": a.name,
                    "type": a.agent_type.value,
                    "completed": a.jobs_completed,
                    "failed": a.jobs_failed,
                    "total_cost": a.total_cost_cents,
                }
                for a in self.agents
            ],
        }

    async def run_stress_test(
        self, duration_seconds: int = 60, ramp_up_seconds: int = 10
    ) -> Dict:
        """Run stress test with gradual ramp-up"""
        print(
            f"\n⚡ Running stress test: {duration_seconds}s duration, {ramp_up_seconds}s ramp-up"
        )

        import random

        results = []
        errors = []
        start = time.perf_counter()
        end_time = start + duration_seconds

        async with aiohttp.ClientSession() as session:
            current_concurrency = 1
            max_concurrency = 50

            async def worker(worker_id: int):
                nonlocal current_concurrency
                while time.perf_counter() < end_time:
                    elapsed = time.perf_counter() - start
                    # Ramp up concurrency
                    if elapsed < ramp_up_seconds:
                        target = int(
                            1 + (max_concurrency - 1) * (elapsed / ramp_up_seconds)
                        )
                        current_concurrency = max(current_concurrency, target)

                    if worker_id >= current_concurrency:
                        await asyncio.sleep(0.5)
                        continue

                    agent = random.choice(self.agents)
                    workflow = random.choice(self.workflows)

                    try:
                        result = await self.simulate_workflow(session, agent, workflow)
                        results.append(result)
                    except Exception as e:
                        errors.append(str(e))

                    await asyncio.sleep(0.05)

            workers = [worker(i) for i in range(max_concurrency)]
            await asyncio.gather(*workers)

        duration = time.perf_counter() - start
        successful = [r for r in results if r.get("success")]

        return {
            "duration_seconds": duration,
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "errors": len(errors),
            "requests_per_second": len(results) / duration,
            "max_concurrency": max_concurrency,
        }


def print_results(title: str, results: Dict):
    """Print formatted results"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    for key, value in results.items():
        if key != "agent_stats":
            print(f"  {key}: {value}")

    if "agent_stats" in results:
        print("\n  Agent Performance:")
        for agent in results["agent_stats"][:5]:  # Top 5
            print(
                f"    {agent['name']}: {agent['completed']} completed, {agent['failed']} failed"
            )


async def main():
    parser = argparse.ArgumentParser(description="AOS Agent Simulation")
    parser.add_argument(
        "--agents", type=int, default=10, help="Number of synthetic agents"
    )
    parser.add_argument(
        "--workflows", type=int, default=100, help="Number of workflows to run"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Concurrent workflows"
    )
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument(
        "--stress-duration", type=int, default=30, help="Stress test duration"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AOS AGENT SIMULATION TEST")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print(f"Agents: {args.agents}")
    print(f"Workflows: {args.workflows}")
    print("=" * 60)

    simulator = AgentSimulator(API_BASE, API_KEY)

    # Create agents and workflows
    simulator.create_synthetic_agents(args.agents)
    simulator.create_test_workflows()

    # Run simulation
    results = await simulator.run_simulation(args.workflows, args.concurrency)
    print_results("Simulation Results", results)

    # Optional stress test
    if args.stress:
        stress_results = await simulator.run_stress_test(args.stress_duration)
        print_results("Stress Test Results", stress_results)

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
