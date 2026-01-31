# Apis — Call Graph

**Domain:** apis  
**Total functions:** 6  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| WRAPPER | 2 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 4 | Terminal — calls no other domain functions |

## Wrappers (thin delegation)

- `keys_driver.KeysDriver.__init__` → ?
- `keys_driver.get_keys_driver` → ?

## Full Call Graph

```
[WRAPPER] keys_driver.KeysDriver.__init__
[LEAF] keys_driver.KeysDriver.fetch_key_by_id
[LEAF] keys_driver.KeysDriver.fetch_key_usage_today
[LEAF] keys_driver.KeysDriver.fetch_keys_paginated
[LEAF] keys_driver.KeysDriver.update_key_frozen
[WRAPPER] keys_driver.get_keys_driver
```
