# Api_Keys — Software Bible

**Domain:** api_keys  
**L2 Features:** 10  
**Scripts:** 4  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for api_keys is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/api_keys/api_keys_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/api_keys/api_keys_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> api_keys_public.py -> L4 registry.execute(...)
- Current status: api_keys_public.py remains scaffold-only (no behavior change yet); existing domain routers stay active during incremental rollout.

## Reality Delta (2026-02-16, PR-9 API Keys List Facade Contract Hardening)

- API keys public facade now implements a concrete read slice at:
- `backend/app/hoc/api/cus/api_keys/api_keys_public.py`
- Endpoint added:
- `GET /cus/api_keys/list` (gateway: `/hoc/api/cus/api_keys/list`)
- Boundary contract now enforces:
- strict query allowlist (`status`, `limit`, `offset`)
- explicit `as_of` rejection in PR-9
- single dispatch path:
- `api_keys_public.py -> registry.execute("api_keys.query", method="list_api_keys", ...)`
- Deterministic list ordering hardened in L6 at:
- `backend/app/hoc/cus/api_keys/L6_drivers/api_keys_facade_driver.py`
- with ordering: `created_at desc, id desc`.

## Reality Delta (2026-02-11)

- Canonical API key ownership is consolidated under:
- `backend/app/hoc/api/cus/api_keys/`
- Read surface:
- `aos_api_key.py` (`/api-keys`)
- Write surface:
- `api_key_writes.py` (`/tenant/api-keys`)
- URL policy decision is split-read/split-write for backward compatibility, while keeping single domain ownership (`api_keys`).
- Legacy onboarding wrappers under `api/cus/policies/` for api keys were deleted.
- Onboarding state advancement on first key creation is retained in `api_key_writes.py` via `_maybe_advance_to_api_key_created`.

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 target-scope classification for api_keys is complete:
- `9` scripts total (`5 UC_LINKED`, `4 NON_UC_SUPPORT`, `0 UNLINKED` in target scope).
- UC-linked api_keys scripts are mapped to `UC-002` in canonical linkage docs.
- Deterministic gates remain clean post-wave and governance suite reports `308` passing tests.
- Audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| api_keys_facade | L5 | `APIKeysFacade.list_api_keys` | CANONICAL | 1 | ?:aos_api_key | ?:__init__ | L5:__init__ | L4:api_keys_handler | YES |
| keys_engine | L5 | `KeysWriteEngine.freeze_key` | CANONICAL | 1 | L3:customer_keys_adapter | L5:customer_keys_adapter | YES |
| api_keys_facade_driver | L6 | `APIKeysFacadeDriver.count_api_keys` | LEAF | 1 | L5:api_keys_facade, api_keys_facade | YES |
| keys_driver | L6 | `KeysDriver.count_keys` | LEAF | 0 | L3:customer_keys_adapter | L5:keys_shim | L5:keys_engine, keys_engine | YES |

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 10 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### DELETE /cache
```
L2:embedding.clear_embedding_cache → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /cache/stats
```
L2:embedding.embedding_cache_stats → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /config
```
L2:embedding.get_embedding_config → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /health
```
L2:embedding.embedding_health → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /iaec/instructions
```
L2:embedding.get_iaec_instructions → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /iaec/segment-info
```
L2:embedding.get_iaec_segment_info → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### GET /quota
```
L2:embedding.get_embedding_quota → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### POST /compose
```
L2:embedding.compose_embedding → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### POST /decompose
```
L2:embedding.decompose_embedding → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

#### POST /iaec/check-mismatch
```
L2:embedding.check_mismatch → L4:api_keys_handler → L6:api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `APIKeysFacade.list_api_keys` | api_keys_facade | CANONICAL | 1 | 6 | no | api_keys_facade_driver:APIKeysFacadeDriver.count_api_keys |  |
| `KeysWriteEngine.freeze_key` | keys_engine | CANONICAL | 1 | 4 | no | keys_driver:KeysDriver.fetch_key_for_update | keys_driver:Ke |

## Wrapper Inventory

_10 thin delegation functions._

- `api_keys_facade.APIKeysFacade.__init__` → ?
- `keys_driver.KeysDriver.__init__` → ?
- `keys_engine.KeysReadEngine.__init__` → keys_driver:get_keys_driver
- `keys_engine.KeysReadEngine.get_key` → keys_driver:KeysDriver.fetch_key_by_id
- `keys_engine.KeysReadEngine.get_key_usage_today` → keys_driver:KeysDriver.fetch_key_usage
- `keys_engine.KeysReadEngine.list_keys` → keys_driver:KeysDriver.count_keys
- `keys_engine.KeysWriteEngine.__init__` → keys_driver:get_keys_driver
- `keys_driver.get_keys_driver` → ?
- `keys_engine.get_keys_read_engine` → ?
- `keys_engine.get_keys_write_engine` → ?

---

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `api_keys_handler.py` | `ApiKeysQueryHandler`: Replaced `getattr()` dispatch with explicit map (2 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`
