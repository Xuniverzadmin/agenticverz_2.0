"""
Minimal Nova Python SDK
Usage:
    from nova_sdk import NovaClient
    client = NovaClient(api_key="...", base_url="http://127.0.0.1:8000")
    agent_id = client.create_agent("test-agent")
    run_id = client.post_goal(agent_id, "ping")
    status = client.poll_run(agent_id, run_id, timeout=10)
"""

import time
import uuid
from typing import Any, Dict, Optional

import requests


class NovaClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-AOS-Key": api_key})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def create_agent(self, name: str) -> str:
        payload = {"name": name}
        r = self.session.post(self._url("/agents"), json=payload)
        r.raise_for_status()
        data = r.json()
        # Expecting agent_id in response or id
        return data.get("agent_id") or data.get("id") or str(uuid.uuid4())

    def post_goal(self, agent_id: str, goal: str, force_skill: Optional[str] = None) -> str:
        payload = {"goal": goal}
        if force_skill:
            payload["force_skill"] = force_skill
        r = self.session.post(self._url(f"/agents/{agent_id}/goals"), json=payload)
        r.raise_for_status()
        data = r.json()
        # try to extract run id from response provenance/plan if present
        run_id = (
            data.get("run_id")
            or data.get("run", {}).get("id")
            or data.get("plan", {}).get("plan_id")
        )
        return run_id

    def poll_run(
        self, agent_id: str, run_id: str, timeout: int = 30, interval: float = 0.5
    ) -> Dict[str, Any]:
        end = time.time() + timeout
        while time.time() < end:
            r = self.session.get(self._url(f"/agents/{agent_id}/runs/{run_id}"))
            if r.status_code == 200:
                data = r.json()
                status = (
                    data.get("status")
                    or data.get("run", {}).get("status")
                    or data.get("plan", {}).get("status")
                )
                if status and status in ("succeeded", "failed"):
                    return data
            time.sleep(interval)
        raise TimeoutError(f"Run {run_id} did not complete in {timeout}s")

    def recall(self, agent_id: str, query: str, k: int = 5) -> Dict[str, Any]:
        params = {"query": query, "k": k}
        r = self.session.get(self._url(f"/agents/{agent_id}/recall"), params=params)
        r.raise_for_status()
        return r.json()

    # =========== Machine-Native APIs (M5.5) ===========

    def simulate(
        self,
        plan: list,
        budget_cents: int = 1000,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Simulate a plan before execution.

        Args:
            plan: List of steps, each with "skill" and "params"
            budget_cents: Available budget in cents
            agent_id: Optional agent ID for permission checking
            tenant_id: Optional tenant ID for isolation

        Returns:
            Simulation result with feasibility, costs, risks, etc.

        Example:
            result = client.simulate([
                {"skill": "http_call", "params": {"url": "https://api.example.com"}},
                {"skill": "llm_invoke", "params": {"prompt": "Summarize this"}}
            ])
            if result["feasible"]:
                print(f"Plan is feasible, cost: {result['estimated_cost_cents']}c")
        """
        payload = {
            "plan": plan,
            "budget_cents": budget_cents,
        }
        if agent_id:
            payload["agent_id"] = agent_id
        if tenant_id:
            payload["tenant_id"] = tenant_id

        r = self.session.post(self._url("/api/v1/runtime/simulate"), json=payload)
        r.raise_for_status()
        return r.json()

    def query(
        self,
        query_type: str,
        params: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query runtime state.

        Supported query types:
        - remaining_budget_cents: Current budget remaining
        - what_did_i_try_already: Previous execution attempts
        - allowed_skills: List of available skills
        - last_step_outcome: Most recent execution outcome
        - skills_available_for_goal: Skills matching a goal

        Args:
            query_type: Type of query to execute
            params: Query-specific parameters
            agent_id: Optional agent ID for context
            run_id: Optional run ID for context

        Returns:
            Query result
        """
        payload = {
            "query_type": query_type,
            "params": params or {},
        }
        if agent_id:
            payload["agent_id"] = agent_id
        if run_id:
            payload["run_id"] = run_id

        r = self.session.post(self._url("/api/v1/runtime/query"), json=payload)
        r.raise_for_status()
        return r.json()

    def list_skills(self) -> Dict[str, Any]:
        """
        List all available skills.

        Returns:
            Dict with skills list, count, and descriptors
        """
        r = self.session.get(self._url("/api/v1/runtime/skills"))
        r.raise_for_status()
        return r.json()

    def describe_skill(self, skill_id: str) -> Dict[str, Any]:
        """
        Get detailed descriptor for a skill.

        Args:
            skill_id: The skill to describe

        Returns:
            Skill descriptor with cost model, failure modes, etc.
        """
        r = self.session.get(self._url(f"/api/v1/runtime/skills/{skill_id}"))
        r.raise_for_status()
        return r.json()

    def get_capabilities(
        self, agent_id: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available capabilities for an agent/tenant.

        Args:
            agent_id: Optional agent ID
            tenant_id: Optional tenant ID

        Returns:
            Capabilities including skills, budget, rate limits, permissions
        """
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        if tenant_id:
            params["tenant_id"] = tenant_id

        r = self.session.get(self._url("/api/v1/runtime/capabilities"), params=params)
        r.raise_for_status()
        return r.json()

    def get_resource_contract(self, resource_id: str) -> Dict[str, Any]:
        """
        Get resource contract for a specific resource.

        Args:
            resource_id: The resource to get contract for

        Returns:
            Resource contract with budget, rate limits, concurrency info
        """
        r = self.session.get(self._url(f"/api/v1/runtime/resource-contract/{resource_id}"))
        r.raise_for_status()
        return r.json()
