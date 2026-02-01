# cus_credential_service.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/cus_credential_service.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            cus_credential_service.py
Lives in:        services/
Role:            Services
Inbound:         cus_health_engine, cus_health_driver
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Customer Credential Service
Violations:      none
```

## Purpose

Customer Credential Service

PURPOSE:
    Secure handling of customer LLM API credentials.
    Encrypts credentials at rest, provides vault-ready integration.

SECURITY PRINCIPLES:
    1. NO PLAINTEXT PERSISTENCE: All stored credentials are encrypted
    2. ROTATION-READY: Credentials can be rotated without downtime
    3. AUDIT TRAIL: All credential access is logged
    4. MINIMAL EXPOSURE: Decryption only at point of use

CREDENTIAL REFERENCE FORMAT:
    - vault://<path>         - HashiCorp Vault reference
    - encrypted://<id>       - Locally encrypted (AES-256-GCM)
    - env://<var_name>       - Environment variable (dev only)

ENCRYPTION:
    - Algorithm: AES-256-GCM
    - Key derivation: PBKDF2 with per-tenant salt
    - In production: KEK from external key management service

## Import Analysis

**External:**
- `cryptography.hazmat.primitives.ciphers.aead`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `CusCredentialService`

Service for managing customer LLM credentials.

Phase 4: Secure credential storage and retrieval.
Production deployments should use external vault integration.

#### Methods

- `__init__(master_key: Optional[bytes])` — Initialize credential service.
- `_derive_dev_key() -> bytes` — Derive a development key (NOT SECURE FOR PRODUCTION).
- `_derive_tenant_key(tenant_id: str) -> bytes` — Derive a tenant-specific encryption key.
- `encrypt_credential(tenant_id: str, plaintext: str, context: Optional[Dict[str, str]]) -> str` — Encrypt a credential for storage.
- `decrypt_credential(tenant_id: str, credential_ref: str, context: Optional[Dict[str, str]]) -> str` — Decrypt a credential reference.
- `resolve_credential(tenant_id: str, credential_ref: str, context: Optional[Dict[str, str]]) -> str` — Resolve a credential reference to plaintext.
- `_resolve_vault_credential(credential_ref: str) -> str` — Resolve a HashiCorp Vault credential reference.
- `_resolve_env_credential(credential_ref: str) -> str` — Resolve an environment variable credential reference.
- `rotate_credential(tenant_id: str, old_credential_ref: str, new_plaintext: str, context: Optional[Dict[str, str]]) -> Tuple[str, bool]` — Rotate a credential (encrypt new, verify old is different).
- `validate_credential_format(credential_ref: str) -> Tuple[bool, str]` — Validate credential reference format without decrypting.
- `generate_master_key() -> str` — Generate a new master encryption key.
- `mask_credential(credential_ref: str) -> str` — Mask a credential reference for logging/display.

## Domain Usage

**Callers:** cus_health_engine, cus_health_driver

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CusCredentialService
      methods:
        - encrypt_credential
        - decrypt_credential
        - resolve_credential
        - rotate_credential
        - validate_credential_format
        - generate_master_key
        - mask_credential
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['cryptography.hazmat.primitives.ciphers.aead']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

