# Integrations Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase 3 Directory Restructure (PIN-470)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

| Attribute | Value |
|-----------|-------|
| Lock Date | 2026-01-24 |
| Lock Version | 1.0.0 |
| BLCA Baseline | 0 violations |
| Phase 3 Fixes | COMPLETE |

---

## Domain Nature

> **Integrations is a CONNECTIVITY domain — it manages external service connections and data bridges.**

Integrations domain:
- **Connects** — external APIs, databases, cloud services
- **Bridges** — cross-domain data flow
- **Adapts** — translates external formats to internal models
- **Secures** — credential management, vault integration

Integrations does NOT:
- Execute business policies (→ Policies domain)
- Track incidents (→ Incidents domain)
- Manage user accounts (→ Account domain)

---

## Locked Artifacts

### L3 Adapters (L3_adapters/) — 26 files

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `cloud_functions_adapter.py` | LOCKED | 2026-01-24 | Cloud functions integration |
| `customer_activity_adapter.py` | LOCKED | 2026-01-24 | Activity domain bridge |
| `customer_incidents_adapter.py` | LOCKED | 2026-01-24 | Incidents domain bridge |
| `customer_keys_adapter.py` | LOCKED | 2026-01-24 | API keys domain bridge |
| `customer_killswitch_adapter.py` | LOCKED | 2026-01-24 | Killswitch integration |
| `customer_logs_adapter.py` | LOCKED | 2026-01-24 | Logs domain bridge |
| `customer_policies_adapter.py` | LOCKED | 2026-01-24 | Policies domain bridge |
| `file_storage_base.py` | LOCKED | 2026-01-24 | File storage base class |
| `founder_contract_review_adapter.py` | LOCKED | 2026-01-24 | Contract review bridge |
| `founder_ops_adapter.py` | LOCKED | 2026-01-24 | Founder ops bridge |
| `gcs_adapter.py` | LOCKED | 2026-01-24 | Google Cloud Storage |
| `lambda_adapter.py` | LOCKED | 2026-01-24 | AWS Lambda integration |
| `notifications_base.py` | LOCKED | 2026-01-24 | Notifications base class |
| `pgvector_adapter.py` | LOCKED | 2026-01-24 | PGVector integration |
| `pinecone_adapter.py` | LOCKED | 2026-01-24 | Pinecone vector DB |
| `policy_adapter.py` | LOCKED | 2026-01-24 | Policy integration |
| `runtime_adapter.py` | LOCKED | 2026-01-24 | Runtime integration |
| `s3_adapter.py` | LOCKED | 2026-01-24 | AWS S3 integration |
| `serverless_base.py` | LOCKED | 2026-01-24 | Serverless base class |
| `slack_adapter.py` | LOCKED | 2026-01-24 | Slack integration |
| `smtp_adapter.py` | LOCKED | 2026-01-24 | SMTP email integration |
| `vector_stores_base.py` | LOCKED | 2026-01-24 | Vector stores base class |
| `weaviate_adapter.py` | LOCKED | 2026-01-24 | Weaviate vector DB |
| `webhook_adapter.py` | LOCKED | 2026-01-24 | Webhook integration |
| `workers_adapter.py` | LOCKED | 2026-01-24 | Workers integration |
| `__init__.py` | LOCKED | 2026-01-24 | Adapter exports |

### L5 Engines (L5_engines/) — 21 files

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `bridges.py` | LOCKED | 2026-01-24 | Bridge logic (L6→L5 reclassified) |
| `connectors_facade.py` | LOCKED | 2026-01-24 | Connectors management |
| `cost_bridges_engine.py` | LOCKED | 2026-01-24 | Cost bridges logic |
| `cost_safety_rails.py` | LOCKED | 2026-01-24 | Cost safety (L6→L5 reclassified) |
| `cost_snapshots.py` | LOCKED | 2026-01-24 | Cost snapshots (L6→L5 reclassified) |
| `cus_health_engine.py` | LOCKED | 2026-01-24 | Customer health logic |
| `datasources_facade.py` | LOCKED | 2026-01-24 | Datasources management |
| `dispatcher.py` | LOCKED | 2026-01-24 | Dispatcher logic (L6→L5 reclassified) |
| `graduation_engine.py` | LOCKED | 2026-01-24 | Graduation logic |
| `http_connector.py` | LOCKED | 2026-01-24 | HTTP connector |
| `iam_engine.py` | LOCKED | 2026-01-24 | IAM logic |
| `identity_resolver.py` | LOCKED | 2026-01-24 | Identity resolution (L6→L5 reclassified) |
| `integrations_facade.py` | LOCKED | 2026-01-24 | Main integrations facade |
| `learning_proof_engine.py` | LOCKED | 2026-01-24 | Learning proof logic |
| `mcp_connector.py` | LOCKED | 2026-01-24 | MCP connector |
| `prevention_contract.py` | LOCKED | 2026-01-24 | Prevention contracts |
| `retrieval_facade.py` | LOCKED | 2026-01-24 | Retrieval facade |
| `retrieval_mediator.py` | LOCKED | 2026-01-24 | Retrieval mediation |
| `sql_gateway.py` | LOCKED | 2026-01-24 | SQL gateway |
| `types.py` | LOCKED | 2026-01-24 | Type definitions |
| `credentials/` | LOCKED | 2026-01-24 | Credential types (L6→L5 reclassified) |
| `__init__.py` | LOCKED | 2026-01-24 | Engine exports |

### L5 Schemas (L5_schemas/) — 6 files

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `audit_schemas.py` | LOCKED | 2026-01-24 | Audit schema definitions |
| `cost_snapshot_schemas.py` | LOCKED | 2026-01-24 | Cost snapshot schemas |
| `cus_schemas.py` | LOCKED | 2026-01-24 | Customer schemas |
| `datasource_model.py` | LOCKED | 2026-01-24 | Datasource model |
| `loop_events.py` | LOCKED | 2026-01-24 | Loop event schemas |
| `__init__.py` | LOCKED | 2026-01-24 | Schema exports |

### L5 Vault (L5_vault/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `drivers/vault.py` | LOCKED | 2026-01-24 | Vault driver |
| `engines/cus_credential_engine.py` | LOCKED | 2026-01-24 | Credential engine |
| `engines/service.py` | LOCKED | 2026-01-24 | Vault service |

### L6 Drivers (L6_drivers/) — 6 files

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `bridges_driver.py` | LOCKED | 2026-01-24 | Bridges DB operations |
| `connector_registry.py` | LOCKED | 2026-01-24 | Connector registry |
| `execution.py` | LOCKED | 2026-01-24 | Execution tracking |
| `external_response_driver.py` | LOCKED | 2026-01-24 | External response storage |
| `knowledge_plane.py` | LOCKED | 2026-01-24 | Knowledge plane operations |
| `__init__.py` | LOCKED | 2026-01-24 | Driver exports |

---

## Phase 3 L5/L6 Reclassification

Files reclassified from L6→L5 based on content analysis (no DB ops):

| File | Old Layer | New Layer | Reason |
|------|-----------|-----------|--------|
| `bridges.py` | L6 | L5 | Pure bridge logic, no Session imports |
| `cost_safety_rails.py` | L6 | L5 | Pure safety logic, no Session imports |
| `cost_snapshots.py` | L6 | L5 | Pure snapshot logic, no Session imports |
| `dispatcher.py` | L6 | L5 | Pure dispatch logic, no Session imports |
| `identity_resolver.py` | L6 | L5 | Pure identity logic, no Session imports |
| `credentials/types.py` | L6 | L5 | Pure type definitions, no Session imports |

---

## Governance Invariants

| ID | Rule | Status | Enforcement |
|----|------|--------|-------------|
| **INV-INT-001** | L5 cannot import sqlalchemy at runtime | COMPLIANT | BLCA |
| **INV-INT-002** | L6 drivers pure data access | COMPLIANT | BLCA |
| **INV-INT-003** | L3 adapters thin translation only | COMPLIANT | Architecture |
| **INV-INT-004** | Facades delegate, never query directly | COMPLIANT | Architecture |

---

## Lock Rules

### What Is Locked

1. **Layer assignments** — No file may change its declared layer
2. **File locations** — No file may move between directories
3. **Import boundaries** — L5 engines cannot add sqlalchemy imports
4. **Adapter boundaries** — L3 adapters < 200 LOC, no state mutation

### What Is Allowed (Without Unlock)

1. **Bug fixes** — Within existing file boundaries
2. **Documentation** — Comments, docstrings
3. **Type hints** — Adding TYPE_CHECKING imports
4. **Test coverage** — New tests for existing code

### Unlock Procedure

To modify locked artifacts:
1. Create unlock request with justification
2. Run BLCA after changes
3. Update this lock document
4. Re-lock domain

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock — Phase 3 Directory Restructure complete. 6 L5 engine files reclassified L6→L5. PIN-470. | Claude |

---

**END OF DOMAIN LOCK**
