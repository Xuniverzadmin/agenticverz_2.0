# Layer: L7 — Legacy Shim (DEPRECATED — DISCONNECTED)
# AUDIENCE: INTERNAL
# Role: DISCONNECTED legacy shim — no longer imports from HOC
# Status: DISCONNECTED (2026-01-31) — legacy↔HOC link severed
#
# Previously re-exported from:
#   app.hoc.cus.policies.L5_engines.lessons_engine
#
# This shim is now EMPTY. Callers should migrate to direct HOC imports:
#   from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine
#
# TODO: Delete this file once all legacy callers are verified migrated.
# Reference: PIN-468, PIN-495

"""
Lessons Engine - DISCONNECTED LEGACY SHIM

This file previously re-exported from the HOC policies domain.
The legacy↔HOC connection has been severed (2026-01-31).

All callers should use the canonical HOC path:
    from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine
"""
