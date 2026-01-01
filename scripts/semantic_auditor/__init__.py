# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Semantic Auditor Package Root
# Authority: None (observational only)
# Callers: CLI, scheduled jobs
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Semantic Auditor - Phase 1 MVP

An observational tooling package that produces risk reports by analyzing
semantic contracts and codebase behavior. This is NOT a CI gate - it's a
background observer that surfaces semantic deltas without blocking.

Key signals detected (Phase 1):
- MISSING_SEMANTIC_HEADER: Boundary files without semantic headers
- ASYNC_BLOCKING_CALL: async def calling blocking I/O
- WRITE_OUTSIDE_WRITE_SERVICE: DB writes outside *_write_service*.py
- LAYER_IMPORT_VIOLATION: Import graph violations
"""

__version__ = "0.1.0"
__author__ = "AgenticVerz Team"
