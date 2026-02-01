# Api_Keys — Software Bible

**Domain:** api_keys  
**L2 Features:** 10  
**Scripts:** 4  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

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
