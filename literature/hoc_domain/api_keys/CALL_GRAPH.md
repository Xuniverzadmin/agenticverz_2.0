# Api_Keys — Call Graph

**Domain:** api_keys  
**Total functions:** 25  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 2 | Owns the algorithm — most decisions, primary logic |
| WRAPPER | 10 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 11 | Terminal — calls no other domain functions |
| ENTRY | 2 | Entry point — no domain-internal callers |

## Canonical Algorithm Owners

### `api_keys_facade.APIKeysFacade.list_api_keys`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 6
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** api_keys_facade.APIKeysFacade.list_api_keys → api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys → api_keys_facade_driver.APIKeysFacadeDriver.fetch_api_keys
- **Calls:** api_keys_facade_driver:APIKeysFacadeDriver.count_api_keys, api_keys_facade_driver:APIKeysFacadeDriver.fetch_api_keys

### `keys_engine.KeysWriteEngine.freeze_key`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 4
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** keys_engine.KeysWriteEngine.freeze_key → keys_driver.KeysDriver.fetch_key_for_update → keys_driver.KeysDriver.update_key_frozen
- **Calls:** keys_driver:KeysDriver.fetch_key_for_update, keys_driver:KeysDriver.update_key_frozen

## Wrappers (thin delegation)

- `api_keys_facade.APIKeysFacade.__init__` → ?
- `keys_driver.KeysDriver.__init__` → ?
- `keys_driver.get_keys_driver` → ?
- `keys_engine.KeysReadEngine.__init__` → keys_driver:get_keys_driver
- `keys_engine.KeysReadEngine.get_key` → keys_driver:KeysDriver.fetch_key_by_id
- `keys_engine.KeysReadEngine.get_key_usage_today` → keys_driver:KeysDriver.fetch_key_usage
- `keys_engine.KeysReadEngine.list_keys` → keys_driver:KeysDriver.count_keys
- `keys_engine.KeysWriteEngine.__init__` → keys_driver:get_keys_driver
- `keys_engine.get_keys_read_engine` → ?
- `keys_engine.get_keys_write_engine` → ?

## Full Call Graph

```
[WRAPPER] api_keys_facade.APIKeysFacade.__init__
[ENTRY] api_keys_facade.APIKeysFacade.get_api_key_detail → api_keys_facade_driver:APIKeysFacadeDriver.fetch_api_key_by_id
[CANONICAL] api_keys_facade.APIKeysFacade.list_api_keys → api_keys_facade_driver:APIKeysFacadeDriver.count_api_keys, api_keys_facade_driver:APIKeysFacadeDriver.fetch_api_keys
[LEAF] api_keys_facade.get_api_keys_facade
[LEAF] api_keys_facade_driver.APIKeysFacadeDriver.count_api_keys
[LEAF] api_keys_facade_driver.APIKeysFacadeDriver.fetch_api_key_by_id
[LEAF] api_keys_facade_driver.APIKeysFacadeDriver.fetch_api_keys
[WRAPPER] keys_driver.KeysDriver.__init__
[LEAF] keys_driver.KeysDriver.count_keys
[LEAF] keys_driver.KeysDriver.fetch_key_by_id
[LEAF] keys_driver.KeysDriver.fetch_key_for_update
[LEAF] keys_driver.KeysDriver.fetch_key_usage
[LEAF] keys_driver.KeysDriver.fetch_keys
[LEAF] keys_driver.KeysDriver.update_key_frozen
[LEAF] keys_driver.KeysDriver.update_key_unfrozen
[WRAPPER] keys_driver.get_keys_driver
[WRAPPER] keys_engine.KeysReadEngine.__init__ → keys_driver:get_keys_driver
[WRAPPER] keys_engine.KeysReadEngine.get_key → keys_driver:KeysDriver.fetch_key_by_id
[WRAPPER] keys_engine.KeysReadEngine.get_key_usage_today → keys_driver:KeysDriver.fetch_key_usage
[WRAPPER] keys_engine.KeysReadEngine.list_keys → keys_driver:KeysDriver.count_keys, keys_driver:KeysDriver.fetch_keys
[WRAPPER] keys_engine.KeysWriteEngine.__init__ → keys_driver:get_keys_driver
[CANONICAL] keys_engine.KeysWriteEngine.freeze_key → keys_driver:KeysDriver.fetch_key_for_update, keys_driver:KeysDriver.update_key_frozen
[ENTRY] keys_engine.KeysWriteEngine.unfreeze_key → keys_driver:KeysDriver.fetch_key_for_update, keys_driver:KeysDriver.update_key_unfrozen
[WRAPPER] keys_engine.get_keys_read_engine
[WRAPPER] keys_engine.get_keys_write_engine
```
