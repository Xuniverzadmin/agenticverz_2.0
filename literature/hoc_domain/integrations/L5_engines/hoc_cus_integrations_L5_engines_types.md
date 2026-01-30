# hoc_cus_integrations_L5_engines_types

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/types.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Canonical Credential dataclass for connector services

## Intent

**Role:** Canonical Credential dataclass for connector services
**Reference:** PIN-470, INT-DUP-001 (Quarantine Resolution)
**Callers:** http_connector.py, mcp_connector.py, sql_gateway.py

## Purpose

Credential Type — Canonical Definition

---

## Classes

### `Credential`
- **Docstring:** Credential from vault.
- **Class Variables:** value: str, expires_at: Optional[datetime]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

http_connector.py, mcp_connector.py, sql_gateway.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: Credential
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
