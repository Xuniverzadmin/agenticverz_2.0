# PIN-517: cus_vault Authority Refactor

**Status:** COMPLETE
**Date:** 2026-02-03
**Predecessor:** PIN-516 (MCP Customer Integration)
**Reference:** First-Principles Vault Analysis

---

## Problem Statement

The vault architecture had **authority confusion** between:
- *Vault selection* — which provider to use
- *Vault resolution* — translating refs to secrets
- *Vault execution* — actual secret retrieval

Two critical gaps:
1. `cus_credential_engine.py:294` — `vault://` resolution raised NotImplementedError
2. `vault.py:742` — AWS Secrets Manager fell back silently to EnvCredentialVault

Root issue: **cus_vault was not enforcing access rules** — it claimed to support `vault://` but could not enforce policy/audit.

---

## Trust Zone Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM TRUST ZONE                        │
│  vault_1 (scope="system")                                   │
│  - Dev/test credentials                                     │
│  - Infra secrets                                            │
│  - Controlled by platform                                   │
│  - env:// allowed (dev only)                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   CUSTOMER TRUST ZONE                       │
│  cus_vault (scope="customer")                               │
│  - Customer-owned secrets                                   │
│  - Accessed only via rule check + intent                    │
│  - SDK-visible, audit-required                              │
│  - env:// FORBIDDEN (silent fallback = credential leak)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Gap Analysis & Fixes

| Gap | Issue | Fix |
|-----|-------|-----|
| GAP-1 | Async boundary violation | Keep vault resolution sync; async rule check at L4 only |
| GAP-2 | Ambiguous credential refs | Lock format: `cus-vault://<tenant_id>/<credential_id>` |
| GAP-3 | Mutable accessor state | Pass accessor per-call, never instance fields |
| GAP-4 | Permissive default | Fail-closed for customer scope |
| GAP-5 | AWS namespace collision | Include `{env}` in secret path |
| GAP-6 | No SDK contract test | Add explicit rule governance test |

---

## Implementation Summary

### FIX 1: Wire HashiCorpVault into cus_credential_engine

**File:** `app/hoc/cus/hoc_spine/services/cus_credential_engine.py`

- Added `resolve_cus_vault_credential()` async method
- Parses `cus-vault://<tenant_id>/<credential_id>` format
- Validates via `CredentialAccessRuleChecker` before vault access
- Sync `resolve_credential()` raises for cus-vault:// (requires async)

### FIX 2: Split vault factory by authority

**File:** `app/hoc/cus/integrations/L5_vault/drivers/vault.py`

- `create_credential_vault(scope="system"|"customer")` factory
- Customer scope: Rejects env vault, requires VAULT_TOKEN for hashicorp
- System scope: Allows env vault fallback for development

### FIX 3: Implement AwsSecretsManagerVault

**File:** `app/hoc/cus/integrations/L5_vault/drivers/vault.py`

- Full AWS Secrets Manager implementation using boto3
- Environment isolation in secret path (GAP-5): `agenticverz/{env}/{tenant}/{cred}`
- Role assumption support for cross-account access

### FIX 4: Enforce access intent (rule check + audit)

**File:** `app/hoc/cus/integrations/L5_vault/engines/vault_rule_check.py` (NEW)

- `CredentialAccessResult` — Frozen dataclass for rule decision
- `CredentialAccessRuleChecker` — Protocol for async rule validation
- `DefaultCredentialAccessRuleChecker` — Permissive (system scope)
- `DenyAllRuleChecker` — Fail-closed (customer scope default)

---

## Files Changed

| Action | File |
|--------|------|
| CREATE | `app/hoc/cus/integrations/L5_vault/__init__.py` |
| CREATE | `app/hoc/cus/integrations/L5_vault/drivers/__init__.py` |
| CREATE | `app/hoc/cus/integrations/L5_vault/engines/__init__.py` |
| CREATE | `app/hoc/cus/integrations/L5_vault/engines/vault_rule_check.py` |
| MODIFY | `app/hoc/cus/integrations/L5_vault/drivers/vault.py` |
| MODIFY | `app/hoc/cus/integrations/L5_vault/engines/service.py` |
| MODIFY | `app/hoc/cus/hoc_spine/services/cus_credential_engine.py` |
| CREATE | `tests/test_cus_vault_sdk_contract.py` |

---

## Credential Reference Scheme

| Format | Scope | Resolution | Rule Check Required |
|--------|-------|------------|---------------------|
| `cus-vault://<tenant_id>/<credential_id>` | Customer | Async via CredentialService | YES |
| `encrypted://<base64>` | Both | Sync AES-256-GCM | NO |
| `env://<VAR_NAME>` | System only | Sync os.environ | NO |
| `vault://...` (legacy) | REJECTED | N/A | N/A |

---

## SDK Contract Tests (GAP-6)

**File:** `tests/test_cus_vault_sdk_contract.py` (10 tests)

| Test Class | Tests | Purpose |
|------------|-------|---------|
| TestCusCredentialServiceContract | 3 | cus-vault:// async, legacy rejection, plaintext rejection |
| TestVaultFactoryContract | 3 | Customer env rejection, VAULT_TOKEN requirement, system env allowed |
| TestCredentialAccessRuleContract | 2 | Default allows, DenyAll blocks |
| TestCredentialReferenceFormat | 2 | Format parsing, encrypted roundtrip |

**Run:** `PYTHONPATH=. python3 -m pytest tests/test_cus_vault_sdk_contract.py -v`

---

## Verification

```bash
# 1. Import checks (no circular imports)
PYTHONPATH=. python3 -c "from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService; print('OK')"

# 2. Customer scope fails without explicit provider
python3 -c "
from app.hoc.cus.integrations.L5_vault.drivers.vault import create_credential_vault
import os
os.environ['CREDENTIAL_VAULT_PROVIDER'] = 'env'
try:
    create_credential_vault(scope='customer')
    print('FAIL: should have raised')
except ValueError as e:
    print(f'OK: {e}')
"

# 3. System scope allows env fallback
CREDENTIAL_VAULT_PROVIDER=env python3 -c "
from app.hoc.cus.integrations.L5_vault.drivers.vault import create_credential_vault
v = create_credential_vault(scope='system')
print(f'OK: {type(v).__name__}')
"

# 4. SDK contract tests pass
PYTHONPATH=. python3 -m pytest tests/test_cus_vault_sdk_contract.py -v
```

---

## SDK Readiness Checklist

- [x] Credential refs are stable strings (`cus-vault://<tenant>/<cred>`)
- [x] No provider details leak to SDK (provider inferred from env, not ref)
- [x] Audit + rule check enforced centrally (at L4, before vault access)
- [x] Provider rotation is transparent (same ref, different provider)
- [x] No silent fallback for customer scope (fail-hard)
- [x] env:// forbidden for customer credentials
- [x] Async boundary is explicit (rule check at L4, vault sync)
- [x] No mutable accessor state (per-call only)
- [x] Fail-closed for customer scope without rule checker
- [x] AWS namespace includes environment
- [x] SDK contract test locks invariants
