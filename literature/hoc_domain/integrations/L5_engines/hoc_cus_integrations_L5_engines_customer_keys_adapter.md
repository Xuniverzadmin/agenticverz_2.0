# hoc_cus_integrations_L5_engines_customer_keys_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/customer_keys_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer API keys boundary adapter (L2 → L3 → L4)

## Intent

**Role:** Customer API keys boundary adapter (L2 → L3 → L4)
**Reference:** PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 L3 Closure)
**Callers:** guard.py (L2) — to be wired

## Purpose

Customer Keys Boundary Adapter (L3)

---

## Functions

### `get_customer_keys_adapter(session: Session) -> CustomerKeysAdapter`
- **Async:** No
- **Docstring:** Get a CustomerKeysAdapter instance.  Args:
- **Calls:** CustomerKeysAdapter

## Classes

### `CustomerKeyInfo(BaseModel)`
- **Docstring:** Customer-safe API key information.
- **Class Variables:** id: str, name: str, prefix: str, status: str, created_at: str, last_seen_at: Optional[str], requests_today: int, spend_today_cents: int

### `CustomerKeyListResponse(BaseModel)`
- **Docstring:** Customer key list response.
- **Class Variables:** items: List[CustomerKeyInfo], total: int

### `CustomerKeyAction(BaseModel)`
- **Docstring:** Result of a key action (freeze/unfreeze).
- **Class Variables:** id: str, name: str, status: str, message: str

### `CustomerKeysAdapter`
- **Docstring:** Boundary adapter for customer API key operations.
- **Methods:** __init__, list_keys, get_key, freeze_key, unfreeze_key

## Attributes

- `__all__` (line 298)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.api_keys.L5_engines.keys_engine` |
| Cross-Domain | `app.hoc.cus.api_keys.L5_engines.keys_engine` |
| External | `pydantic`, `sqlmodel` |

## Callers

guard.py (L2) — to be wired

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_keys_adapter
      signature: "get_customer_keys_adapter(session: Session) -> CustomerKeysAdapter"
  classes:
    - name: CustomerKeyInfo
      methods: []
    - name: CustomerKeyListResponse
      methods: []
    - name: CustomerKeyAction
      methods: []
    - name: CustomerKeysAdapter
      methods: [list_keys, get_key, freeze_key, unfreeze_key]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
