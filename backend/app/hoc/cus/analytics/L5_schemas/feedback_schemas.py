# capability_id: CAP-002
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: L5-safe feedback DTO for pattern detection engine
# Callers: pattern_detection.py (L5)
# Allowed Imports: pydantic (DTO framework)
# Forbidden Imports: L1, L2, L3, L7 (app.models)
# Reference: PIN-520 Phase 3 (L5 purity — no runtime app.models imports)
# artifact_class: CODE

"""
Pattern feedback DTO mirror.

Mirrors app.models.feedback.PatternFeedbackCreate so that L5 engines
never need a runtime import of app.models. Fields MUST stay in sync
with the L7 original.

Canonical source: app/models/feedback.py
"""

from typing import Optional

from pydantic import BaseModel


class PatternFeedbackCreate(BaseModel):
    """Input model for creating pattern feedback.

    Mirror of app.models.feedback.PatternFeedbackCreate.
    """

    tenant_id: str
    pattern_type: str
    severity: str = "info"
    description: str
    signature: Optional[str] = None
    provenance: list[str] = []
    occurrence_count: int = 1
    time_window_minutes: Optional[int] = None
    threshold_used: Optional[str] = None
    metadata: Optional[dict] = None
