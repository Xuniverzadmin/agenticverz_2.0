# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Integrated Runtime (M2)
# runtime/integrated_runtime.py
"""
Integrated Runtime (M2)

Runtime that fetches handlers from SkillRegistry v2 instead of
internal registry map. Provides full machine-native interface
with registry-backed skill resolution.
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

_app_path = str(Path(__file__).parent.parent.parent)

    sys.path.insert(0, _app_path)

# Import registry_v2 directly to avoid triggering skills/__init__.py with pydantic
from skills.registry_v2 import SkillRegistry, get_global_registry

from .core import ErrorCategory, Runtime, SkillDescriptor, SkillHandler, StructuredOutcome


class IntegratedRuntime(Runtime):
    """
    Runtime integrated with SkillRegistry v2.

    This runtime extends the base Runtime to fetch handlers from
    the skill registry rather than maintaining its own internal map.

    Features:
    - Registry-backed skill resolution
    - Version selection support
    - Fallback to internal registry for backwards compatibility
    """

    def __init__(self, registry: Optional[SkillRegistry] = None):
        """
        Initialize integrated runtime.

        Args:
            registry: SkillRegistry instance (uses global if None)
        """
        super().__init__()
        self._registry = registry

    @property
    def registry(self) -> SkillRegistry:
        """Get the registry instance."""
        if self._registry is not None:
            return self._registry
        return get_global_registry()

    def register_skill(self, descriptor: SkillDescriptor, handler: SkillHandler) -> None:
        """
        Register a skill with both runtime and registry.

        This maintains backwards compatibility with the base Runtime
        while also registering with the SkillRegistry.
        """
        # Register with base runtime
        super().register_skill(descriptor, handler)

        # Also register with registry
        try:
            self.registry.register(descriptor, handler)
        except ValueError:
            # Already registered in registry, ignore
            pass

    async def execute(
        self, skill_id: str, inputs: Mapping[str, Any], timeout_s: Optional[float] = None, version: Optional[str] = None
    ) -> StructuredOutcome:
        """
        Execute a skill with registry-backed resolution.

        Args:
            skill_id: The skill to execute
            inputs: Input parameters for the skill
            timeout_s: Optional timeout in seconds
            version: Optional specific version to use

        Returns:
            StructuredOutcome with ok=True/False and result/error
        """
        start_ts = time.time()
        call_id = str(uuid.uuid4())
        meta = {
            "call_id": call_id,
            "skill_id": skill_id,
            "started_at": start_ts,
            "inputs_hash": hash(frozenset(inputs.items())) if inputs else 0,
            "version_requested": version,
        }

        # Try registry first
        registration = self.registry.resolve(skill_id, version)

        if registration is not None:
            handler = registration.handler
            descriptor = registration.descriptor
            meta["version_resolved"] = registration.version
            meta["is_stub"] = registration.is_stub
        else:
            # Fallback to internal registry
            if skill_id not in self._registry_internal:
                meta["ended_at"] = time.time()
                meta["duration_s"] = meta["ended_at"] - start_ts
                outcome = StructuredOutcome.failure(
                    call_id=call_id,
                    code="ERR_SKILL_NOT_FOUND",
                    message=f"Skill not found: {skill_id}",
                    category=ErrorCategory.PERMANENT,
                    retryable=False,
                    meta=meta,
                )
                self._record_execution(skill_id, inputs, outcome)
                return outcome

            handler = self._registry[skill_id]
            descriptor = self._skill_descriptors.get(skill_id)

        # Get cost model
        if descriptor:
            estimated_cost = descriptor.cost_model.get("base_cents", 0)
        else:
            estimated_cost = 0

        # Check budget
        if self._budget_spent_cents + estimated_cost > self._budget_total_cents:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_BUDGET_EXCEEDED",
                message=f"Budget exceeded: {self._budget_spent_cents}/{self._budget_total_cents} cents",
                category=ErrorCategory.RESOURCE,
                retryable=False,
                meta=meta,
            )
            self._record_execution(skill_id, inputs, outcome)
            return outcome

        # Execute handler
        try:
            coro = handler(inputs)
            if timeout_s is not None:
                result = await asyncio.wait_for(coro, timeout=timeout_s)
            else:
                result = await coro

            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            meta["cost_cents"] = estimated_cost
            self._budget_spent_cents += estimated_cost

            outcome = StructuredOutcome.success(call_id, result, meta)
            self._record_execution(skill_id, inputs, outcome)
            return outcome

        except asyncio.TimeoutError:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_TIMEOUT",
                message=f"Execution timed out after {timeout_s}s",
                category=ErrorCategory.TRANSIENT,
                retryable=True,
                meta=meta,
            )
            self._record_execution(skill_id, inputs, outcome)
            return outcome

        except Exception as exc:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_RUNTIME_EXCEPTION",
                message=str(exc),
                category=ErrorCategory.PERMANENT,
                retryable=False,
                meta={**meta, "exception_type": type(exc).__name__},
            )
            self._record_execution(skill_id, inputs, outcome)
            return outcome

    @property
    def _registry_internal(self) -> Dict[str, SkillHandler]:
        """Access to internal registry for fallback."""
        return self._registry

    def describe_skill(self, skill_id: str) -> Optional[SkillDescriptor]:
        """
        Return stable descriptor for a skill.

        Checks registry first, then falls back to internal.
        """
        # Try registry
        reg = self.registry.resolve(skill_id)
        if reg:
            return reg.descriptor

        # Fallback to internal
        return self._skill_descriptors.get(skill_id)

    async def query(self, query_type: str, **params: Any) -> Dict[str, Any]:
        """
        Query interface with registry integration.

        Extends base query with registry-aware responses.
        """
        if query_type == "allowed_skills":
            # Combine registry and internal skills
            registry_skills = self.registry.get_all_skill_ids()
            internal_skills = list(self._registry.keys())
            all_skills = list(set(registry_skills + internal_skills))
            return {
                "skills": all_skills,
                "count": len(all_skills),
                "from_registry": len(registry_skills),
                "from_internal": len(internal_skills),
            }

        elif query_type == "skill_manifest":
            # Get full manifest from registry
            return {"manifest": self.registry.get_manifest()}

        # Delegate other queries to base
        return await super().query(query_type, **params)

    def get_all_skills(self) -> List[str]:
        """Get list of all registered skill IDs from both sources."""
        registry_skills = self.registry.get_all_skill_ids()
        internal_skills = list(self._registry.keys())
        return list(set(registry_skills + internal_skills))


def create_integrated_runtime(
    registry: Optional[SkillRegistry] = None, register_stubs: bool = True
) -> IntegratedRuntime:
    """
    Factory function to create an integrated runtime with optional stubs.

    Args:
        registry: SkillRegistry instance (uses global if None)
        register_stubs: Whether to register default stubs

    Returns:
        Configured IntegratedRuntime
    """
    runtime = IntegratedRuntime(registry)

    if register_stubs:
        # Register default stubs
        from app.hoc.int.agent.engines import (
            HTTP_CALL_STUB_DESCRIPTOR,
            JSON_TRANSFORM_STUB_DESCRIPTOR,
            LLM_INVOKE_STUB_DESCRIPTOR,
            http_call_stub_handler,
            json_transform_stub_handler,
            llm_invoke_stub_handler,
        )

        runtime.register_skill(HTTP_CALL_STUB_DESCRIPTOR, http_call_stub_handler)
        runtime.register_skill(LLM_INVOKE_STUB_DESCRIPTOR, llm_invoke_stub_handler)
        runtime.register_skill(JSON_TRANSFORM_STUB_DESCRIPTOR, json_transform_stub_handler)

    return runtime
