# PIN-486: L3 Adapters Absorbed — Files Redistributed to L2/L4/L5

**Status:** ✅ COMPLETE
**Created:** 2026-01-28
**Category:** Architecture

---

## Summary

## L3 Adapter Absorption — COMPLETE

V2.0.0 abolished the L3 layer. All 28 files from _deprecated_L3/ have been classified and moved to their correct locations. _deprecated_L3/ directory deleted.

### Classification Rule Applied
- Translation/formatting/SDK wrappers → L2 (Adapter) in cus/{domain}/adapters/
- System-level translation → L4 HOC Spine (Adapter) in hoc_spine/adapters/
- Business logic → L5 Domain Engine in cus/{domain}/L5_engines/

### Files Moved — Integration SDK Wrappers (13 files)
Source: _deprecated_L3/integrations_L3_adapters/
Target: cus/integrations/adapters/
- s3_adapter.py — AWS S3 file storage
- gcs_adapter.py — Google Cloud Storage
- lambda_adapter.py — AWS Lambda invocation
- cloud_functions_adapter.py — Google Cloud Functions
- slack_adapter.py — Slack notification delivery
- smtp_adapter.py — SMTP email delivery
- webhook_adapter.py — Webhook delivery with circuit breaker
- pinecone_adapter.py — Pinecone vector store
- weaviate_adapter.py — Weaviate vector store
- pgvector_adapter.py — PostgreSQL pgvector
- file_storage_base.py — Abstract file storage interface
- serverless_base.py — Abstract serverless interface
- vector_stores_base.py — Abstract vector store interface

### Files Moved — Customer-Facing Domain Adapters (6 files)
- customer_incidents_adapter.py → cus/incidents/adapters/
- customer_policies_adapter.py → cus/policies/adapters/
- customer_keys_adapter.py → cus/api_keys/adapters/
- customer_logs_adapter.py → cus/logs/adapters/
- customer_activity_adapter.py → cus/activity/adapters/
- customer_killswitch_adapter.py → cus/controls/adapters/

### Files Moved — Founder-Facing Adapters (2 files)
- founder_ops_adapter.py → cus/incidents/adapters/
- founder_contract_review_adapter.py → cus/policies/adapters/

### Files Moved — Domain Policy/Worker Adapters (2 files)
- policy_adapter.py → cus/policies/adapters/
- workers_adapter.py → cus/activity/adapters/

### Files Moved — HOC Spine Adapters (2 files)
Target: hoc_spine/adapters/
- runtime_adapter.py — Delegates to L4 commands
- alert_delivery.py — Pure HTTP to Alertmanager

### Files Moved — Analytics Adapter (1 file)
- v2_adapter.py → cus/analytics/adapters/

### Files Moved — Consequences Adapter (1 file)
- export_bundle_adapter.py → hoc_spine/consequences/adapters/

### Files Moved — Business Logic to L5 (1 file)
- anomaly_bridge.py → cus/incidents/L5_engines/ (applies incident creation thresholds)

### Header Updates
- All files: # Layer: L3 → # Layer: L2 — Adapter (domain) or # Layer: L4 — HOC Spine (Adapter)
- All docstrings/comments: L3 references replaced with Adapter
- Flow references: L2 → L3 → L4 updated to L2 → L4
- Logger names: L3_adapters → adapters
- anomaly_bridge.py: Header changed to L5 — Domain Engine

### New Directory Structure
cus/{domain}/adapters/ created for: integrations, incidents, policies, api_keys, logs, activity, controls, analytics
hoc_spine/adapters/ created
hoc_spine/consequences/adapters/ created
Each directory has __init__.py

### Deleted
- _deprecated_L3/ — entire directory removed (was holding 33 files for human review)

### Reference
- Supersedes: Phase 6 of V2_MIGRATION_MANIFEST.md (L3 deprecation)
- PIN-485 (V2.0.0 migration complete)
- HOC_LAYER_TOPOLOGY_V2.0.0.md (L3 removal binding constraint)

---

## Details

[Add details here]
