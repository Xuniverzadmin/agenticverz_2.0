# Api_Keys — Domain Capability

**Domain:** api_keys  
**Total functions:** 25  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for api_keys is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/api_keys/api_keys_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/api_keys/api_keys_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> api_keys_public.py -> L4 registry.execute(...)
- Current status: api_keys_public.py remains scaffold-only (no behavior change yet); existing domain routers stay active during incremental rollout.

## Reality Delta (2026-02-11)

- API key domain now owns both read and write lifecycles at L2 under:
- `backend/app/hoc/api/cus/api_keys/`
- Write operations are no longer hosted in `logs/tenants.py`; they are in:
- `backend/app/hoc/api/cus/api_keys/api_key_writes.py`
- Active lifecycle endpoints:
- `GET /api-keys`, `GET /api-keys/{id}` (read)
- `GET/POST/DELETE /tenant/api-keys` (write/revoke/list)
- Onboarding transition hook on first key create remains active and DB-backed.

## 1. Domain Purpose

Manages API key lifecycle — creation, rotation, revocation, and usage tracking for machine-native access.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `APIKeysFacade.get_api_key_detail` | api_keys_facade | Yes | L4:api_keys_handler | pure |
| `APIKeysFacade.list_api_keys` | api_keys_facade | Yes | L4:api_keys_handler | pure |
| `get_api_keys_facade` | api_keys_facade | Yes | L4:api_keys_handler | pure |

## 3. Internal Functions

### Helpers

_4 internal helper functions._

- **api_keys_facade:** `APIKeysFacade.__init__`
- **keys_driver:** `KeysDriver.__init__`
- **keys_engine:** `KeysReadEngine.__init__`, `KeysWriteEngine.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `APIKeysFacadeDriver.count_api_keys` | api_keys_facade_driver | db_write |
| `APIKeysFacadeDriver.fetch_api_key_by_id` | api_keys_facade_driver | db_write |
| `APIKeysFacadeDriver.fetch_api_keys` | api_keys_facade_driver | db_write |
| `KeysDriver.count_keys` | keys_driver | pure |
| `KeysDriver.fetch_key_by_id` | keys_driver | pure |
| `KeysDriver.fetch_key_for_update` | keys_driver | pure |
| `KeysDriver.fetch_key_usage` | keys_driver | pure |
| `KeysDriver.fetch_keys` | keys_driver | pure |
| `KeysDriver.update_key_frozen` | keys_driver | db_write |
| `KeysDriver.update_key_unfrozen` | keys_driver | db_write |
| `get_keys_driver` | keys_driver | pure |

### Unclassified (needs review)

_7 functions need manual classification._

- `KeysReadEngine.get_key` (keys_engine)
- `KeysReadEngine.get_key_usage_today` (keys_engine)
- `KeysReadEngine.list_keys` (keys_engine)
- `KeysWriteEngine.freeze_key` (keys_engine)
- `KeysWriteEngine.unfreeze_key` (keys_engine)
- `get_keys_read_engine` (keys_engine)
- `get_keys_write_engine` (keys_engine)

## 4. Explicit Non-Features

_No explicit non-feature declarations found in API_KEYS_DOMAIN_LOCK_FINAL.md._
