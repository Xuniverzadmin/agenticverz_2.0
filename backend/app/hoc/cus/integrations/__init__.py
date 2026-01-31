# Layer: L5 — Domain (Integrations)
# NOTE: Header corrected L4→L5 (2026-01-31) — this is a domain package, not L4 spine
# AUDIENCE: CUSTOMER
# Role: Integrations domain - LLM provider management, connectors, retrieval mediation
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, HOC_integrations_analysis_v1.md

"""
Integrations Domain

Topics: providers, health, limits, connectors, datasources, mediation, credentials
Roles: facades, engines, schemas, vault

DOMAIN PERSONA DECLARATION
==========================

Integrations serves three personas:

1. CUSTOMER CONSOLE — BYOK LLM integrations, datasources, limits
   - Key files: cus_integration_service.py, integrations_facade.py

2. PLATFORM RUNTIME — Connector registries, lifecycle, health
   - Key files: connector_registry.py, *_connector.py

3. MEDIATION LAYER — Deny-by-default retrieval, evidence emission
   - Key files: retrieval_mediator.py, retrieval_facade.py

TRANSITIONAL FILES (Phase 5 Migration)
======================================

Some engines are AUDIENCE: INTERNAL but currently live here:
- server_registry.py → will move to internal/platform/mcp/engines/
- vault.py → will move to internal/platform/vault/engines/

These files are quarantined with import guards. New customer-facing code
MUST NOT import them directly. Access only through facades or protocols.

GOVERNANCE INVARIANTS
=====================

INV-INT-001: LLM never constructs raw SQL (template-only)
INV-INT-002: LLM never controls base URL (machine-controlled)
INV-INT-003: Deny-by-default mediation (policy check before execution)
INV-INT-004: Tenant isolation (tenant_id verification everywhere)
INV-INT-005: No plaintext credentials (AES-256-GCM encryption)
INV-INT-006: INTERNAL files are quarantined (no new customer imports)
"""
