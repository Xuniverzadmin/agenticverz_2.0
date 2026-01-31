# Layer: L5 — Domain (API Keys)
# NOTE: Header corrected L4→L5 (2026-01-31) — this is a domain package, not L4 spine
# AUDIENCE: CUSTOMER
# Role: API Keys domain - Programmatic access
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, HOC_api_keys_analysis_v1.md

"""
API Keys Domain

Topics: keys, permissions, usage
Roles: facades, engines, schemas

DOMAIN CONTRACT
===============

API Keys is a small, security-sensitive domain. Clarity matters more
than code volume here.

ENTRY POINT HIERARCHY:

  1. APIKeysFacade (facades/api_keys_facade.py)
     - CUSTOMER-FACING entry point
     - Async (AsyncSession)
     - READ-ONLY operations
     - Synthetic keys filtered out
     - Callers: L2 API routes only

  2. KeysReadService / KeysWriteService (engines/keys_service.py)
     - OPERATIONAL PRIMITIVES
     - Sync (Session)
     - Read + Write operations
     - Callers: L3 adapters, runtime, gateway — NOT L2

CALLER RULE:

  L2 APIs MUST use APIKeysFacade.
  L2 APIs MUST NOT call engines directly.

INVARIANTS:

  INV-KEY-001: API key state changes must be explicit, auditable, and reversible
  INV-KEY-002: No implicit mutation during read paths
  INV-KEY-003: Synthetic keys never exposed to customer facade

ASYNC/SYNC SPLIT (Intentional):

  - Facade is async (modern API handlers)
  - Engine is sync (runtime/gateway compatibility)
  - This is intentional, not technical debt
"""
