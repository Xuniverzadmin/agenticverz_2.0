# Business Builder Worker Agents
# Agent definitions using M15 SBA Schema
"""
Each agent has a Strategy Cascade that:
1. Defines WHY the agent exists (winning_aspiration)
2. Defines BOUNDARIES (where_to_play)
3. Defines TASKS (how_to_win)
4. Defines DEPENDENCIES (capabilities_capacity)
5. Defines GOVERNANCE (enabling_management_systems)

These agents are:
- Registered via M12 agent registry
- Routed via M17 CARE engine
- Governed via M19 policy layer
- Evolved via M18 CARE-L
"""

from .definitions import (
    WORKER_AGENTS,
    create_copywriter_agent,
    create_governor_agent,
    create_recovery_agent,
    create_researcher_agent,
    create_strategist_agent,
    create_ux_agent,
    create_validator_agent,
    register_all_agents,
)

__all__ = [
    "create_researcher_agent",
    "create_strategist_agent",
    "create_copywriter_agent",
    "create_ux_agent",
    "create_recovery_agent",
    "create_governor_agent",
    "create_validator_agent",
    "WORKER_AGENTS",
    "register_all_agents",
]
