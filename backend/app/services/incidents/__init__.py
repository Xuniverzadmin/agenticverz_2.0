# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Incidents domain services module
# Callers: Incidents API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md

"""
Incidents Domain Services

L4 services for incident analysis and post-mortem:
- IncidentPatternService: Detect structural patterns (category_cluster, severity_spike, cascade_failure)
- RecurrenceAnalysisService: Analyze recurring incident types
- PostMortemService: Extract learnings from resolved incidents

Design Rules:
- All services are read-only (no writes)
- No cross-service calls
- SQL-based analytics only
"""

from app.services.incidents.facade import (
    IncidentFacade,
    get_incident_facade,
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
from app.services.incidents.recurrence_analysis_service import (
    RecurrenceAnalysisService,
    RecurrenceGroup,
    RecurrenceResult,
)

__all__ = [
    # Facade (external access point)
    "IncidentFacade",
    "get_incident_facade",
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
