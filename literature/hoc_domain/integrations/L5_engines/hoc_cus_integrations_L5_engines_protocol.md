# hoc_cus_integrations_L5_engines_protocol

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/credentials/protocol.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Canonical CredentialService protocol for connector services

## Intent

**Role:** Canonical CredentialService protocol for connector services
**Reference:** PIN-470, INT-DUP-002 (Quarantine Resolution)
**Callers:** http_connector.py, mcp_connector.py, sql_gateway.py

## Purpose

CredentialService Protocol — Canonical Definition

---

## Classes

### `CredentialService(Protocol)`
- **Docstring:** Protocol for credential service.
- **Methods:** get

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `types` |

## Callers

http_connector.py, mcp_connector.py, sql_gateway.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CredentialService
      methods: [get]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
