# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: hoc/cus/policies (sandbox execution)
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch) | internal tools
#   Execution: async
# Role: L4 handler — policy-domain sandbox execution boundary (GAP-174)
# Callers: OperationRegistry (L4) via operation "policies.sandbox_execute"
# Allowed Imports: hoc_spine, hoc.cus.policies.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: GAP-174 (Execution Sandboxing), HOC_LAYER_TOPOLOGY_V2.0.0
# artifact_class: CODE

"""
Policies Sandbox Handler (GAP-174)

Provides an L4-owned call path for policy sandbox execution so the sandbox
engine is a live execution dependency (not just a wired import).
"""

from __future__ import annotations

from typing import Any, Optional

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class PoliciesSandboxExecuteHandler:
    """Handler for policies.sandbox_execute."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        code = ctx.params.get("code")
        language = ctx.params.get("language")
        policy_id: Optional[str] = ctx.params.get("policy_id")
        environment: Optional[dict[str, str]] = ctx.params.get("environment")
        files: Optional[dict[str, Any]] = ctx.params.get("files")
        user_id: Optional[str] = ctx.params.get("user_id")
        run_id: Optional[str] = ctx.params.get("run_id")
        metadata: Optional[dict[str, Any]] = ctx.params.get("metadata")

        if not isinstance(code, str) or not code.strip():
            return OperationResult.fail("Missing required param: code", "MISSING_CODE")
        if not isinstance(language, str) or not language.strip():
            return OperationResult.fail("Missing required param: language", "MISSING_LANGUAGE")

        from app.hoc.cus.policies.L5_engines.sandbox_engine import (
            ExecutionRequest,
            get_sandbox_service,
        )

        service = get_sandbox_service()
        request = ExecutionRequest(
            code=code,
            language=language,
            policy_id=policy_id,
            environment=environment,
            files=files,
            tenant_id=ctx.tenant_id,
            user_id=user_id,
            run_id=run_id,
            metadata=metadata or {},
        )

        result = await service.execute(request)
        return OperationResult.ok(result.to_dict())


def register(registry: OperationRegistry) -> None:
    """Register policies sandbox operations with the registry."""
    registry.register("policies.sandbox_execute", PoliciesSandboxExecuteHandler())

