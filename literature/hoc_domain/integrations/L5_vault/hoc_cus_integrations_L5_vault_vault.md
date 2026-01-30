# hoc_cus_integrations_L5_vault_vault

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_vault/drivers/vault.py` |
| Layer | L6 — Domain Driver |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Credential vault abstraction with multiple provider support

## Intent

**Role:** Credential vault abstraction with multiple provider support
**Reference:** PIN-470, GAP-171 (Credential Vault Integration), HOC_integrations_analysis_v1.md
**Callers:** CredentialService

## Purpose

Credential Vault Abstraction (GAP-171)

---

## Functions

### `create_credential_vault() -> CredentialVault`
- **Async:** No
- **Docstring:** Factory function to create appropriate vault based on configuration.
- **Calls:** EnvCredentialVault, HashiCorpVault, getenv, info, warning

## Classes

### `VaultProvider(str, Enum)`
- **Docstring:** Supported vault providers.

### `CredentialType(str, Enum)`
- **Docstring:** Types of credentials.

### `CredentialMetadata`
- **Docstring:** Metadata about a stored credential (without secret values).
- **Class Variables:** credential_id: str, tenant_id: str, name: str, credential_type: CredentialType, description: Optional[str], tags: list[str], created_at: datetime, updated_at: datetime, expires_at: Optional[datetime], last_accessed_at: Optional[datetime], access_count: int, is_rotatable: bool, rotation_interval_days: Optional[int], metadata: Dict[str, Any]

### `CredentialData`
- **Docstring:** Full credential including secret values.
- **Methods:** credential_id, tenant_id
- **Class Variables:** metadata: CredentialMetadata, secret_data: Dict[str, str]

### `CredentialVault(ABC)`
- **Docstring:** Abstract credential vault interface.
- **Methods:** store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential

### `HashiCorpVault(CredentialVault)`
- **Docstring:** HashiCorp Vault implementation.
- **Methods:** __init__, store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential

### `EnvCredentialVault(CredentialVault)`
- **Docstring:** Environment variable credential vault (development only).
- **Methods:** __init__, store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential

## Attributes

- `logger` (line 46)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `httpx` |

## Callers

CredentialService

## Export Contract

```yaml
exports:
  functions:
    - name: create_credential_vault
      signature: "create_credential_vault() -> CredentialVault"
  classes:
    - name: VaultProvider
      methods: []
    - name: CredentialType
      methods: []
    - name: CredentialMetadata
      methods: []
    - name: CredentialData
      methods: [credential_id, tenant_id]
    - name: CredentialVault
      methods: [store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential]
    - name: HashiCorpVault
      methods: [store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential]
    - name: EnvCredentialVault
      methods: [store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
