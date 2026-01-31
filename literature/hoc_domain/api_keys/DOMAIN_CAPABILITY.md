# Api_Keys — Domain Capability

**Domain:** api_keys  
**Total functions:** 25  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

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
