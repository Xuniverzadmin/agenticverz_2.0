"""
AOS Python SDK Client

Usage:
    from aos_sdk import AOSClient
    client = AOSClient(api_key="...", base_url="http://127.0.0.1:8000")

    # Machine-native APIs
    caps = client.get_capabilities()
    result = client.simulate([{"skill": "http_call", "params": {"url": "..."}}])

    # Agent workflow
    agent_id = client.create_agent("my-agent")
    run_id = client.post_goal(agent_id, "ping")
    status = client.poll_run(agent_id, run_id)
"""

from typing import Optional, Dict, Any, List
import time
import uuid
import os

try:
    import httpx
    _USE_HTTPX = True
except ImportError:
    import requests
    _USE_HTTPX = False


class AOSError(Exception):
    """Base exception for AOS SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AOSClient:
    """
    AOS Python SDK Client.

    Provides access to the Agentic Operating System runtime APIs.

    Args:
        api_key: API key for authentication. If not provided, reads from AOS_API_KEY env var.
        base_url: Base URL of the AOS server. Defaults to http://127.0.0.1:8000.
        timeout: Request timeout in seconds. Defaults to 30.

    Example:
        >>> client = AOSClient(api_key="your-key")
        >>> caps = client.get_capabilities()
        >>> print(f"Available skills: {caps['skills_available']}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://127.0.0.1:8000",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("AOS_API_KEY")
        self.timeout = timeout

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-AOS-Key"] = self.api_key

        if _USE_HTTPX:
            self._client = httpx.Client(headers=headers, timeout=timeout)
        else:
            self._session = requests.Session()
            self._session.headers.update(headers)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request and return JSON response."""
        url = self._url(path)

        try:
            if _USE_HTTPX:
                resp = self._client.request(method, url, json=json, params=params)
                if resp.status_code >= 400:
                    raise AOSError(
                        f"Request failed: {resp.status_code}",
                        status_code=resp.status_code,
                        response=resp.json() if resp.content else None
                    )
                return resp.json() if resp.content else {}
            else:
                resp = self._session.request(method, url, json=json, params=params, timeout=self.timeout)
                if resp.status_code >= 400:
                    raise AOSError(
                        f"Request failed: {resp.status_code}",
                        status_code=resp.status_code,
                        response=resp.json() if resp.content else None
                    )
                return resp.json() if resp.content else {}
        except (httpx.HTTPError if _USE_HTTPX else requests.RequestException) as e:
            raise AOSError(f"Request error: {e}") from e

    # =========== Machine-Native APIs ===========

    def simulate(
        self,
        plan: List[Dict[str, Any]],
        budget_cents: int = 1000,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate a plan before execution.

        Pre-execution validation to check if a plan is feasible given
        current constraints (budget, rate limits, permissions).

        Args:
            plan: List of steps, each with "skill" and "params"
            budget_cents: Available budget in cents
            agent_id: Optional agent ID for permission checking
            tenant_id: Optional tenant ID for isolation

        Returns:
            Simulation result with feasibility, estimated costs, and risks.

        Example:
            >>> result = client.simulate([
            ...     {"skill": "http_call", "params": {"url": "https://api.example.com"}},
            ...     {"skill": "llm_invoke", "params": {"prompt": "Summarize"}}
            ... ])
            >>> if result["feasible"]:
            ...     print(f"Plan OK, cost: {result['estimated_cost_cents']}c")
        """
        payload: Dict[str, Any] = {
            "plan": plan,
            "budget_cents": budget_cents,
        }
        if agent_id:
            payload["agent_id"] = agent_id
        if tenant_id:
            payload["tenant_id"] = tenant_id

        return self._request("POST", "/api/v1/runtime/simulate", json=payload)

    def query(
        self,
        query_type: str,
        params: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None
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
            Query result (structure depends on query type)
        """
        payload: Dict[str, Any] = {
            "query_type": query_type,
            "params": params or {},
        }
        if agent_id:
            payload["agent_id"] = agent_id
        if run_id:
            payload["run_id"] = run_id

        return self._request("POST", "/api/v1/runtime/query", json=payload)

    def list_skills(self) -> Dict[str, Any]:
        """
        List all available skills.

        Returns:
            Dict with skills list and count.

        Example:
            >>> skills = client.list_skills()
            >>> for skill in skills["skills"]:
            ...     print(f"{skill['name']}: {skill['description']}")
        """
        return self._request("GET", "/api/v1/runtime/skills")

    def describe_skill(self, skill_id: str) -> Dict[str, Any]:
        """
        Get detailed descriptor for a skill.

        Args:
            skill_id: The skill to describe (e.g., "http_call", "llm_invoke")

        Returns:
            Skill descriptor with cost model, failure modes, params, etc.
        """
        return self._request("GET", f"/api/v1/runtime/skills/{skill_id}")

    def get_capabilities(
        self,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available capabilities for an agent/tenant.

        Args:
            agent_id: Optional agent ID
            tenant_id: Optional tenant ID

        Returns:
            Capabilities including skills, budget, rate limits, permissions.

        Example:
            >>> caps = client.get_capabilities()
            >>> print(f"Budget: {caps['budget_remaining_cents']}c")
            >>> print(f"Skills: {caps['skills_available']}")
        """
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        if tenant_id:
            params["tenant_id"] = tenant_id

        return self._request("GET", "/api/v1/runtime/capabilities", params=params)

    def get_resource_contract(self, resource_id: str) -> Dict[str, Any]:
        """
        Get resource contract for a specific resource.

        Args:
            resource_id: The resource to get contract for

        Returns:
            Resource contract with budget, rate limits, concurrency info.
        """
        return self._request("GET", f"/api/v1/runtime/resource-contract/{resource_id}")

    # =========== Agent Workflow APIs ===========

    def create_agent(self, name: str) -> str:
        """
        Create a new agent.

        Args:
            name: Name for the agent

        Returns:
            Agent ID
        """
        data = self._request("POST", "/agents", json={"name": name})
        return data.get("agent_id") or data.get("id") or str(uuid.uuid4())

    def post_goal(
        self,
        agent_id: str,
        goal: str,
        force_skill: Optional[str] = None
    ) -> str:
        """
        Post a goal for an agent to execute.

        Args:
            agent_id: Agent ID to execute the goal
            goal: Goal description
            force_skill: Optional skill to force use

        Returns:
            Run ID for tracking execution
        """
        payload: Dict[str, Any] = {"goal": goal}
        if force_skill:
            payload["force_skill"] = force_skill

        data = self._request("POST", f"/agents/{agent_id}/goals", json=payload)
        return (
            data.get("run_id") or
            data.get("run", {}).get("id") or
            data.get("plan", {}).get("plan_id") or
            ""
        )

    def poll_run(
        self,
        agent_id: str,
        run_id: str,
        timeout: int = 30,
        interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Poll for run completion.

        Args:
            agent_id: Agent ID
            run_id: Run ID to poll
            timeout: Maximum wait time in seconds
            interval: Poll interval in seconds

        Returns:
            Run result when completed

        Raises:
            TimeoutError: If run doesn't complete within timeout
        """
        end = time.time() + timeout
        while time.time() < end:
            try:
                data = self._request("GET", f"/agents/{agent_id}/runs/{run_id}")
                status = (
                    data.get("status") or
                    data.get("run", {}).get("status") or
                    data.get("plan", {}).get("status")
                )
                if status and status in ("succeeded", "failed"):
                    return data
            except AOSError:
                pass
            time.sleep(interval)
        raise TimeoutError(f"Run {run_id} did not complete in {timeout}s")

    def recall(
        self,
        agent_id: str,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Query agent memory.

        Args:
            agent_id: Agent ID
            query: Search query
            k: Number of results to return

        Returns:
            Memory recall results
        """
        return self._request(
            "GET",
            f"/agents/{agent_id}/recall",
            params={"query": query, "k": k}
        )

    # =========== Run Management APIs ===========

    def create_run(
        self,
        agent_id: str,
        goal: str,
        plan: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a new run for an agent.

        Args:
            agent_id: Agent ID
            goal: Goal description
            plan: Optional pre-defined plan

        Returns:
            Run creation response with run_id
        """
        payload: Dict[str, Any] = {
            "agent_id": agent_id,
            "goal": goal,
        }
        if plan:
            payload["plan"] = plan

        return self._request("POST", "/api/v1/runs", json=payload)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """
        Get run status and details.

        Args:
            run_id: Run ID

        Returns:
            Run details including status, outcome, metrics
        """
        return self._request("GET", f"/api/v1/runs/{run_id}")

    def close(self):
        """Close the client and release resources."""
        if _USE_HTTPX:
            self._client.close()
        else:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Backwards compatibility alias
NovaClient = AOSClient
