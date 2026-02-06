# hoc_cus_logs_L5_engines_certificate

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/certificate.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cryptographic certificate generation for deterministic replay

## Intent

**Role:** Cryptographic certificate generation for deterministic replay
**Reference:** PIN-470, PIN-240
**Callers:** guard.py (replay endpoint)

## Purpose

M23 Certificate Service - Cryptographic Evidence of Deterministic Replay

---

## Classes

### `CertificateType(str, Enum)`
- **Docstring:** Types of certificates that can be issued.

### `CertificatePayload`
- **Docstring:** The signed payload of a certificate.
- **Methods:** to_dict, canonical_json
- **Class Variables:** certificate_id: str, certificate_type: CertificateType, call_id: str, determinism_level: str, match_achieved: str, validation_passed: bool, tenant_id: Optional[str], user_id: Optional[str], policy_count: int, policies_passed: int, policies_failed: int, model_id: str, model_drift_detected: bool, issued_at: str, valid_until: str, request_hash: Optional[str], response_hash: Optional[str]

### `Certificate`
- **Docstring:** A signed certificate proving deterministic replay or policy evaluation.
- **Methods:** to_dict, to_json, from_dict
- **Class Variables:** payload: CertificatePayload, signature: str, version: str

### `CertificateService`
- **Docstring:** Service for creating and verifying cryptographic certificates.
- **Methods:** __init__, _sign, _verify_signature, create_replay_certificate, create_policy_audit_certificate, verify_certificate, export_certificate

## Attributes

- `__all__` (line 381)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.logs.L5_engines.replay_determinism` |

## Callers

guard.py (replay endpoint)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CertificateType
      methods: []
    - name: CertificatePayload
      methods: [to_dict, canonical_json]
    - name: Certificate
      methods: [to_dict, to_json, from_dict]
    - name: CertificateService
      methods: [create_replay_certificate, create_policy_audit_certificate, verify_certificate, export_certificate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
