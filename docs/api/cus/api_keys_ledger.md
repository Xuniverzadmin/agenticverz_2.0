# CUS Domain Ledger: api_keys

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 13
**Unique method+path:** 13

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/api-keys | list_api_keys | List API keys. READ-ONLY. Delegates to L4 operation registry |
| GET | /hoc/api/cus/api-keys/{key_id} | get_api_key_detail | Get API key detail (O3). Delegates to L4 operation registry. |
| GET | /hoc/api/cus/api_keys/list | list_api_keys_public |  |
| DELETE | /hoc/api/cus/embedding/cache | clear_embedding_cache | Clear all embedding cache entries. |
| GET | /hoc/api/cus/embedding/cache/stats | embedding_cache_stats | Get embedding cache statistics. |
| POST | /hoc/api/cus/embedding/compose | compose_embedding | Compose an instruction-aware embedding using IAEC v3.0. |
| GET | /hoc/api/cus/embedding/config | get_embedding_config | Get embedding configuration. |
| POST | /hoc/api/cus/embedding/decompose | decompose_embedding | Decompose an IAEC embedding back into its constituent slots  |
| GET | /hoc/api/cus/embedding/health | embedding_health | Quick health check for embedding subsystem. |
| POST | /hoc/api/cus/embedding/iaec/check-mismatch | check_mismatch | Check instruction-query semantic compatibility (v3.1). |
| GET | /hoc/api/cus/embedding/iaec/instructions | get_iaec_instructions | Get available IAEC instruction types and their weights. |
| GET | /hoc/api/cus/embedding/iaec/segment-info | get_iaec_segment_info | Get IAEC v3.0 segmentation configuration. |
| GET | /hoc/api/cus/embedding/quota | get_embedding_quota | Get current embedding quota status. |
