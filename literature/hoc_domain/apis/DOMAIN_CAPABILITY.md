# Apis — Domain Capability

**Domain:** apis  
**Total functions:** 6  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## 1. Domain Purpose

API discovery and documentation for customer-facing endpoints. Manages API catalog and capability registry.

## 2. Customer-Facing Operations

_No operations classified for this domain._

## 3. Internal Functions

### Helpers

_1 internal helper functions._

- **keys_driver:** `KeysDriver.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `KeysDriver.fetch_key_by_id` | keys_driver | pure |
| `KeysDriver.fetch_key_usage_today` | keys_driver | pure |
| `KeysDriver.fetch_keys_paginated` | keys_driver | pure |
| `KeysDriver.update_key_frozen` | keys_driver | db_write |
| `get_keys_driver` | keys_driver | pure |

## 4. Explicit Non-Features

_No explicit non-feature declarations found in APIS_DOMAIN_LOCK_FINAL.md._
