# hoc_cus_integrations_L5_vault_service

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_vault/engines/service.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

High-level credential service with validation and auditing

## Intent

**Role:** High-level credential service with validation and auditing
**Reference:** PIN-470, GAP-171 (Credential Vault Integration)
**Callers:** ConnectorRegistry, LifecycleHandlers, API routes

## Purpose

Credential Service (GAP-171)

---

## Classes

### `CredentialAccessRecord`
- **Docstring:** Record of credential access for auditing.
- **Class Variables:** credential_id: str, tenant_id: str, accessor_id: str, accessor_type: str, action: str, success: bool, accessed_at: datetime, error_message: Optional[str]

### `CredentialService`
- **Docstring:** High-level credential service.
- **Methods:** __init__, store_credential, get_credential, get_secret_value, list_credentials, update_credential, delete_credential, rotate_credential, get_expiring_credentials, get_rotatable_credentials, get_access_log, _audit, _validate_tenant_id, _validate_name, _validate_secret_data

## Attributes

- `logger` (line 41)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `vault` |

## Callers

ConnectorRegistry, LifecycleHandlers, API routes

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CredentialAccessRecord
      methods: []
    - name: CredentialService
      methods: [store_credential, get_credential, get_secret_value, list_credentials, update_credential, delete_credential, rotate_credential, get_expiring_credentials, get_rotatable_credentials, get_access_log]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
