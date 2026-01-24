# Layer: L4 — Domain Engines
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync/async
# Role: Incidents domain services module
# Callers: Incidents API (L2), worker runtime, governance services
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md, FACADE_CONSOLIDATION_PLAN.md

"""
Incidents Domain Services

L4 services for incident analysis and post-mortem:
- IncidentDriver: INTERNAL driver for worker/governance (use for internal callers)
- IncidentPatternService: Detect structural patterns (category_cluster, severity_spike, cascade_failure)
- RecurrenceAnalysisService: Analyze recurring incident types
- PostMortemService: Extract learnings from resolved incidents

For CUSTOMER API operations, use incidents_facade.py (at services root) instead.

Design Rules:
- All services are read-only (no writes)
- No cross-service calls
- SQL-based analytics only
"""

# NEW: Driver for internal use (workers, governance)
from app.services.incidents.incident_driver import (
    IncidentDriver,
    get_incident_driver,
)

# DEPRECATED: Backward compatibility aliases (will be removed)
# Use get_incident_driver() instead
from app.services.incidents.incident_driver import (
    IncidentFacade,  # Alias for IncidentDriver
    get_incident_facade,  # Alias for get_incident_driver
)
from app.services.incidents.incident_pattern_service import (
    IncidentPatternService,
    PatternMatch,
    PatternResult,
)
from app.services.incidents.postmortem_service import (
    CategoryLearnings,
    LearningInsight,
    PostMortemResult,
    PostMortemService,
    ResolutionSummary,
)
from app.services.incidents.recurrence_analysis_driver import (  # PIN-468 reclassified
    RecurrenceAnalysisService,  # Deprecated alias
    RecurrenceGroup,
    RecurrenceResult,
)

__all__ = [
    # Driver (INTERNAL access point - workers, governance)
    "IncidentDriver",
    "get_incident_driver",
    # DEPRECATED: Backward compatibility aliases
    "IncidentFacade",  # Use IncidentDriver instead
    "get_incident_facade",  # Use get_incident_driver instead
    # Pattern Detection
    "IncidentPatternService",
    "PatternMatch",
    "PatternResult",
    # Recurrence Analysis
    "RecurrenceAnalysisService",
    "RecurrenceGroup",
    "RecurrenceResult",
    # Post-Mortem
    "PostMortemService",
    "PostMortemResult",
    "ResolutionSummary",
    "LearningInsight",
    "CategoryLearnings",
]
