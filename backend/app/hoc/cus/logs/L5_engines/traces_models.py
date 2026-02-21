# capability_id: CAP-001
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure data models)
#   Writes: none
# Role: Re-export trace models from L5_schemas (backward compatibility)
# Callers: L5 engines that haven't migrated imports yet
# Allowed Imports: L5_schemas
# Forbidden Imports: L6, L7, sqlalchemy (runtime)
# Reference: PIN-521 (L5_schemas extraction), PIN-470 Trace System

"""
Trace Models for AOS - BACKWARD COMPATIBILITY RE-EXPORTS

PIN-521 Migration:
- Canonical home is now L5_schemas/traces_models.py
- This file re-exports for backward compatibility
- L6 drivers MUST import from L5_schemas (not here)
- New code SHOULD import from L5_schemas

To migrate existing imports:
    OLD: from app.hoc.cus.logs.L5_engines.traces_models import TraceRecord
    NEW: from app.hoc.cus.logs.L5_schemas.traces_models import TraceRecord
"""

# Re-export from canonical location (L5_schemas)
from app.hoc.cus.logs.L5_schemas.traces_models import (
    ParityResult,
    TraceRecord,
    TraceStatus,
    TraceStep,
    TraceSummary,
    _normalize_for_determinism,
    compare_traces,
)

__all__ = [
    "TraceStatus",
    "TraceStep",
    "TraceSummary",
    "TraceRecord",
    "ParityResult",
    "compare_traces",
    "_normalize_for_determinism",
]
