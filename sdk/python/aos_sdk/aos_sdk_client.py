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

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .aos_sdk_attribution import (
    ActorType,
    AttributionContext,
    AttributionError,
    AttributionErrorCode,
    EnforcementMode,
    create_human_attribution,
    create_service_attribution,
    create_system_attribution,
    get_enforcement_mode,
    is_legacy_override_enabled,
    validate_attribution,
)

try:
    import httpx

    _USE_HTTPX = True
except ImportError:
    import requests

    _USE_HTTPX = False

# =============================================================================
# INVOCATION SAFETY LAYER (PIN-332)
# =============================================================================
# Safety hooks for SDK methods
# Mode: OBSERVE_WARN (v1) - logs warnings, only blocks on plan injection

logger = logging.getLogger(__name__)

try:
    # Try to import from backend (when running in same environment)
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../backend"))
    from app.auth.invocation_safety import (
        InvocationSafetyContext,
        SafetyFlag,
        SDKSafetyHook,
        emit_safety_metrics,
        sdk_safety_hook,
    )

    _SAFETY_LAYER_AVAILABLE = True
except ImportError:
    # Safety layer not available - continue without it (degraded mode)
    _SAFETY_LAYER_AVAILABLE = False
    sdk_safety_hook = None
    InvocationSafetyContext = None


class AOSError(Exception):
    """Base exception for AOS SDK errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class SafetyBlockedError(AOSError):
    """Raised when a safety check blocks execution (PIN-332)."""

    def __init__(self, message: str, flags: Optional[List[str]] = None):
        super().__init__(message)
        self.flags = flags or []


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
        timeout: int = 30,
        tenant_id: Optional[str] = None,
        caller_id: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("AOS_API_KEY")
        self.timeout = timeout
        self.tenant_id = tenant_id or os.getenv("AOS_TENANT_ID")
        self.caller_id = caller_id or os.getenv("AOS_CALLER_ID")

        # Derive caller_id from API key if not explicitly set
        if not self.caller_id and self.api_key:
            self.caller_id = (
                f"sdk:{self.api_key[:8]}" if len(self.api_key) >= 8 else f"sdk:{self.api_key}"
            )

        # Tenant budget limit for safety checks
        self._tenant_budget_limit = int(os.getenv("AOS_TENANT_BUDGET_LIMIT", "10000"))

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-AOS-Key"] = self.api_key

        if _USE_HTTPX:
            self._client = httpx.Client(headers=headers, timeout=timeout)
        else:
            self._session = requests.Session()
            self._session.headers.update(headers)

    # =========== Safety Layer Helpers (PIN-332) ===========

    def _build_safety_context(self) -> Optional["InvocationSafetyContext"]:
        """Build safety context from SDK environment."""
        if not _SAFETY_LAYER_AVAILABLE or InvocationSafetyContext is None:
            return None

        return InvocationSafetyContext(
            caller_id=self.caller_id,
            tenant_id=self.tenant_id,
            tenant_budget_limit=self._tenant_budget_limit,
        )

    def _run_safety_check(self, method: str, result) -> None:
        """
        Process safety check result.

        In OBSERVE_WARN mode (v1):
        - Warnings are logged but don't block
        - Only ERROR severity (plan injection) raises SafetyBlockedError
        """
        if result is None:
            return

        # Emit metrics
        if _SAFETY_LAYER_AVAILABLE:
            emit_safety_metrics("CAP-021", method, result)

        # Log warnings
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"SDK safety warning [{method}]: {warning}")

        # Block on ERROR severity
        if result.blocked:
            raise SafetyBlockedError(
                f"Safety blocked: {result.block_reason}",
                flags=[f.value for f in result.flags],
            )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self, method: str, path: str, json: Optional[Dict] = None, params: Optional[Dict] = None
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
                        response=resp.json() if resp.content else None,
                    )
                return resp.json() if resp.content else {}
            else:
                resp = self._session.request(
                    method, url, json=json, params=params, timeout=self.timeout
                )
                if resp.status_code >= 400:
                    raise AOSError(
                        f"Request failed: {resp.status_code}",
                        status_code=resp.status_code,
                        response=resp.json() if resp.content else None,
                    )
                return resp.json() if resp.content else {}
        except httpx.HTTPError if _USE_HTTPX else requests.RequestException as e:
            raise AOSError(f"Request error: {e}") from e

    # =========== Machine-Native APIs ===========

    def simulate(
        self,
        plan: List[Dict[str, Any]],
        budget_cents: int = 1000,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
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

        Raises:
            SafetyBlockedError: If plan contains forbidden fields (PIN-332 INPUT-003)
        """
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), INPUT-001 (budget), INPUT-003 (plan injection)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                result = sdk_safety_hook.check_simulate(
                    ctx,
                    plan_data={"steps": plan},
                    budget_cents=budget_cents,
                )
                self._run_safety_check("simulate", result)

        # Apply budget cap if needed
        effective_budget = min(budget_cents, self._tenant_budget_limit)
        if effective_budget < budget_cents:
            logger.warning(
                f"Budget {budget_cents} exceeds tenant limit {self._tenant_budget_limit}, using {effective_budget}"
            )

        payload: Dict[str, Any] = {
            "plan": plan,
            "budget_cents": effective_budget,
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
        self, agent_id: Optional[str] = None, tenant_id: Optional[str] = None
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
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                result = sdk_safety_hook.check_create_agent(ctx)
                self._run_safety_check("create_agent", result)

        data = self._request("POST", "/agents", json={"name": name})
        return data.get("agent_id") or data.get("id") or str(uuid.uuid4())

    def post_goal(self, agent_id: str, goal: str, force_skill: Optional[str] = None) -> str:
        """
        Post a goal for an agent to execute.

        Args:
            agent_id: Agent ID to execute the goal
            goal: Goal description
            force_skill: Optional skill to force use (triggers impersonation warning)

        Returns:
            Run ID for tracking execution
        """
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), ID-002 (impersonation via force_skill)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                ctx.agent_id = agent_id
                result = sdk_safety_hook.check_post_goal(ctx, force_skill=force_skill)
                self._run_safety_check("post_goal", result)

        payload: Dict[str, Any] = {"goal": goal}
        if force_skill:
            payload["force_skill"] = force_skill

        data = self._request("POST", f"/agents/{agent_id}/goals", json=payload)
        return (
            data.get("run_id")
            or data.get("run", {}).get("id")
            or data.get("plan", {}).get("plan_id")
            or ""
        )

    def poll_run(
        self, agent_id: str, run_id: str, timeout: int = 30, interval: float = 0.5
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
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), OWN-002 (run ownership), RATE-001 (polling rate)
        # Note: Rate limiting is enforced per poll, not per poll_run call
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                ctx.run_id = run_id
                # Initial check (once per poll_run call)
                result = sdk_safety_hook.check_poll_run(ctx, run_tenant_id=self.tenant_id)
                self._run_safety_check("poll_run", result)

        end = time.time() + timeout
        while time.time() < end:
            try:
                data = self._request("GET", f"/agents/{agent_id}/runs/{run_id}")
                status = (
                    data.get("status")
                    or data.get("run", {}).get("status")
                    or data.get("plan", {}).get("status")
                )
                if status and status in ("succeeded", "failed"):
                    return data
            except AOSError:
                pass
            time.sleep(interval)
        raise TimeoutError(f"Run {run_id} did not complete in {timeout}s")

    def recall(self, agent_id: str, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Query agent memory.

        Args:
            agent_id: Agent ID
            query: Search query
            k: Number of results to return

        Returns:
            Memory recall results
        """
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), OWN-001 (agent ownership)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                ctx.agent_id = agent_id
                result = sdk_safety_hook.check_recall(ctx, agent_tenant_id=self.tenant_id)
                self._run_safety_check("recall", result)

        return self._request("GET", f"/agents/{agent_id}/recall", params={"query": query, "k": k})

    # =========== Run Management APIs ===========

    def create_run(
        self,
        goal: str,
        *,
        agent_id: str,
        actor_type: str,
        origin_system_id: str,
        actor_id: Optional[str] = None,
        plan: Optional[List[Dict]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a new run with required attribution.

        Attribution is REQUIRED per AOS_SDK_ATTRIBUTION_CONTRACT.
        Runs without proper attribution will be rejected.

        Args:
            goal: Goal description / objective for the run
            agent_id: REQUIRED - Executing agent identifier
            actor_type: REQUIRED - HUMAN | SYSTEM | SERVICE
            origin_system_id: REQUIRED - System that initiated this run
            actor_id: REQUIRED if actor_type == HUMAN, must be None otherwise
            plan: Optional pre-defined plan
            **kwargs: Additional run parameters

        Returns:
            Run creation response with run_id

        Raises:
            AttributionError: If attribution validation fails
            SafetyBlockedError: If plan contains forbidden fields (PIN-332 INPUT-003)

        Example:
            >>> # SYSTEM run (automation)
            >>> run = client.create_run(
            ...     goal="Process daily reports",
            ...     agent_id="agent-report-processor",
            ...     actor_type="SYSTEM",
            ...     origin_system_id="cron-scheduler-001",
            ... )

            >>> # HUMAN run (user action)
            >>> run = client.create_run(
            ...     goal="Analyze data",
            ...     agent_id="agent-analyst",
            ...     actor_type="HUMAN",
            ...     actor_id="user_12345",
            ...     origin_system_id="customer-console",
            ... )
        """
        # =========================================================================
        # ATTRIBUTION VALIDATION (Phase 3)
        # Per AOS_SDK_ATTRIBUTION_CONTRACT.md
        # =========================================================================
        attr_ctx = AttributionContext(
            agent_id=agent_id,
            actor_type=actor_type,
            origin_system_id=origin_system_id,
            actor_id=actor_id,
            origin_ts=datetime.now(timezone.utc),
        )

        # Validate BEFORE any network call
        validate_attribution(
            attr_ctx,
            enforcement_mode=get_enforcement_mode(),
            allow_legacy_override=is_legacy_override_enabled(),
        )

        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), INPUT-002 (plan immutability), INPUT-003 (plan injection)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                ctx.agent_id = agent_id
                result = sdk_safety_hook.check_create_run(
                    ctx,
                    plan_data={"steps": plan} if plan else None,
                )
                self._run_safety_check("create_run", result)

        # Build payload with attribution
        payload: Dict[str, Any] = {
            "agent_id": agent_id,
            "goal": goal,
            "actor_type": actor_type.upper(),
            "origin_system_id": origin_system_id,
            **kwargs,
        }

        # actor_id only included when present (HUMAN actors)
        if actor_id is not None:
            payload["actor_id"] = actor_id

        if plan:
            payload["plan"] = plan

        return self._request("POST", "/api/v1/runs", json=payload)

    def create_system_run(
        self,
        goal: str,
        *,
        agent_id: str,
        origin_system_id: str,
        plan: Optional[List[Dict]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a SYSTEM-initiated run.

        Use for: cron jobs, schedulers, policy triggers, automation.
        actor_type is automatically set to SYSTEM.
        actor_id is automatically set to None.

        Args:
            goal: Goal description
            agent_id: REQUIRED - Executing agent identifier
            origin_system_id: REQUIRED - System that initiated this run
            plan: Optional pre-defined plan
            **kwargs: Additional run parameters

        Returns:
            Run creation response with run_id

        Example:
            >>> run = client.create_system_run(
            ...     goal="Process daily reports",
            ...     agent_id="agent-report-processor",
            ...     origin_system_id="cron-scheduler-001",
            ... )
        """
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="SYSTEM",
            origin_system_id=origin_system_id,
            actor_id=None,
            plan=plan,
            **kwargs,
        )

    def create_human_run(
        self,
        goal: str,
        *,
        agent_id: str,
        actor_id: str,
        origin_system_id: str,
        plan: Optional[List[Dict]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a HUMAN-initiated run.

        Use for: user-triggered actions, console operations.
        actor_type is automatically set to HUMAN.
        actor_id is REQUIRED for human runs.

        Args:
            goal: Goal description
            agent_id: REQUIRED - Executing agent identifier
            actor_id: REQUIRED - Human actor identity
            origin_system_id: REQUIRED - System that initiated this run
            plan: Optional pre-defined plan
            **kwargs: Additional run parameters

        Returns:
            Run creation response with run_id

        Example:
            >>> run = client.create_human_run(
            ...     goal="Analyze customer data",
            ...     agent_id="agent-data-analyst",
            ...     actor_id="user_12345",
            ...     origin_system_id="customer-console",
            ... )
        """
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="HUMAN",
            origin_system_id=origin_system_id,
            actor_id=actor_id,
            plan=plan,
            **kwargs,
        )

    def create_service_run(
        self,
        goal: str,
        *,
        agent_id: str,
        origin_system_id: str,
        plan: Optional[List[Dict]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a SERVICE-initiated run.

        Use for: service-to-service calls, internal APIs, workers.
        actor_type is automatically set to SERVICE.
        actor_id is automatically set to None.

        Args:
            goal: Goal description
            agent_id: REQUIRED - Executing agent identifier
            origin_system_id: REQUIRED - System that initiated this run
            plan: Optional pre-defined plan
            **kwargs: Additional run parameters

        Returns:
            Run creation response with run_id

        Example:
            >>> run = client.create_service_run(
            ...     goal="Validate payment",
            ...     agent_id="agent-payment-validator",
            ...     origin_system_id="payment-service-v2",
            ... )
        """
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="SERVICE",
            origin_system_id=origin_system_id,
            actor_id=None,
            plan=plan,
            **kwargs,
        )

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """
        Get run status and details.

        Args:
            run_id: Run ID

        Returns:
            Run details including status, outcome, metrics
        """
        # =========================================================================
        # SAFETY CHECK (PIN-332)
        # =========================================================================
        # Check: ID-001 (identity), OWN-002 (run ownership)
        if _SAFETY_LAYER_AVAILABLE and sdk_safety_hook:
            ctx = self._build_safety_context()
            if ctx:
                ctx.run_id = run_id
                result = sdk_safety_hook.check_get_run(ctx, run_tenant_id=self.tenant_id)
                self._run_safety_check("get_run", result)

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
