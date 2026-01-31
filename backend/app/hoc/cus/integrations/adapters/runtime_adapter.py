# Layer: L3 — Boundary Adapter (Translation)
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Translate API requests into runtime domain commands
# Callers: runtime.py (L2)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-258 Phase F-3 Runtime Cluster
# Contract: PHASE_F_FIX_DESIGN (L3 Adapter Rules)
#
# GOVERNANCE NOTE: This L3 adapter is the ONLY thing L2 runtime.py may call.
# It must NOT import from L5 (workers, execution).
# It translates API requests into L4 domain commands and returns domain results.

"""
Runtime Boundary Adapter (L3)

L3 adapter for runtime API operations. This is the boundary between:
- L2 (API routes) - callers
- L4 (Domain commands) - domain decisions

This adapter:
1. Receives API requests from L2
2. Translates them into L4 domain facts
3. Calls L4 command functions
4. Returns domain results to L2

It does NOT:
- Import from L5 (workers)
- Execute skills directly
- Make domain decisions (that's L4's job)

Reference: PIN-258 Phase F-3 Runtime Cluster
"""

import logging
from typing import Any, Dict, List, Optional

from app.commands.runtime_command import (
    CapabilitiesInfo,
    QueryResult,
    ResourceContractInfo,
    SkillInfo,
    execute_query,
    get_all_skill_descriptors,
    get_capabilities,
    get_resource_contract,
    get_skill_info,
    get_supported_query_types,
    list_skills,
)

logger = logging.getLogger("nova.adapters.runtime")


class RuntimeAdapter:
    """
    L3 Boundary Adapter for runtime operations.

    Translates API requests into L4 domain commands.
    This is the ONLY runtime interface L2 may call.

    Reference: PIN-258 Phase F-3 Runtime Cluster
    """

    def __init__(self):
        """Initialize the adapter."""
        self._logger = logging.getLogger("nova.adapters.runtime")

    def query(
        self,
        query_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Execute a runtime query.

        Translates query request to L4 command and returns domain result.

        Args:
            query_type: Type of query to execute
            params: Query-specific parameters

        Returns:
            QueryResult with query response

        Reference: PIN-258 Phase F-3
        """
        self._logger.debug(f"Runtime query: type={query_type}, params={params}")

        # Delegate to L4 domain command
        result = execute_query(query_type, params)

        self._logger.debug(f"Runtime query result: {result.query_type}")
        return result

    def get_supported_queries(self) -> List[str]:
        """
        Get list of supported query types.

        Returns:
            List of supported query type strings
        """
        return get_supported_query_types()

    def describe_skill(self, skill_id: str) -> Optional[SkillInfo]:
        """
        Get skill description.

        Translates skill lookup to L4 command and returns domain result.

        Args:
            skill_id: Skill identifier

        Returns:
            SkillInfo if skill exists, None otherwise

        Reference: PIN-258 Phase F-3
        """
        self._logger.debug(f"Describe skill: {skill_id}")

        # Delegate to L4 domain command
        return get_skill_info(skill_id)

    def list_skills(self) -> List[str]:
        """
        List all available skills.

        Returns:
            List of skill IDs
        """
        return list_skills()

    def get_skill_descriptors(self) -> Dict[str, Dict[str, Any]]:
        """
        Get descriptors for all skills.

        Returns:
            Dict mapping skill_id to descriptor dict
        """
        return get_all_skill_descriptors()

    def get_resource_contract(self, resource_id: str) -> ResourceContractInfo:
        """
        Get resource contract.

        Translates contract request to L4 command and returns domain result.

        Args:
            resource_id: Resource identifier

        Returns:
            ResourceContractInfo with contract details

        Reference: PIN-258 Phase F-3
        """
        self._logger.debug(f"Get resource contract: {resource_id}")

        # Delegate to L4 domain command
        return get_resource_contract(resource_id)

    def get_capabilities(
        self,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> CapabilitiesInfo:
        """
        Get capabilities for an agent/tenant.

        Translates capability request to L4 command and returns domain result.

        Args:
            agent_id: Optional agent ID
            tenant_id: Optional tenant ID

        Returns:
            CapabilitiesInfo with capability details

        Reference: PIN-258 Phase F-3
        """
        self._logger.debug(f"Get capabilities: agent_id={agent_id}, tenant_id={tenant_id}")

        # Delegate to L4 domain command
        return get_capabilities(agent_id, tenant_id)


# =============================================================================
# Module-level factory function
# =============================================================================


def get_runtime_adapter() -> RuntimeAdapter:
    """
    Factory function to get RuntimeAdapter instance.

    This is the entry point for L2 to get the adapter.

    Returns:
        RuntimeAdapter instance

    Reference: PIN-258 Phase F-3
    """
    return RuntimeAdapter()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "RuntimeAdapter",
    "get_runtime_adapter",
]
