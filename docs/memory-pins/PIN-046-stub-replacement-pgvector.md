# PIN-046: Stub Replacement & pgvector Integration

**Date:** 2025-12-07
**Status:** COMPLETE
**Category:** Infrastructure / Integration
**Session:** M8 Production Hardening - Stub Replacement

---

## Summary

This session completed the replacement of all P0/P1 development stubs with real-world implementations, including the final pgvector upgrade for semantic memory search.

---

## Work Completed

### P0 Items (All Complete)

| Item | Description | Implementation |
|------|-------------|----------------|
| **P0-1** | Clerk Auth (fail-closed) | `app/auth/rbac.py` + `clerk_provider.py` with `RBAC_ENFORCE` flag |
| **P0-2** | Redis Idempotency (Upstash) | `app/traces/idempotency.py` with atomic Lua scripts |
| **P0-3** | Provenance DB (Neon) | `app/costsim/provenance_async.py` + `CostSimProvenanceModel` |
| **P0-4** | Canary Reports Table | `CostSimCanaryReportModel` added to `app/models/costsim_cb.py` |
| **P0-5** | Golden Datasets Store | `app/storage/artifact.py` with pluggable `S3ArtifactStore` (R2 compatible) |

### P1 Items (All Complete)

| Item | Description | Implementation |
|------|-------------|----------------|
| **P1-1** | LLM Adapter (Anthropic) | `app/skills/adapters/claude_adapter.py` - full implementation |
| **P1-2** | Memory Backend (pgvector) | `app/memory/vector_store.py` - semantic search |
| **P1-3** | Dev Token Guard | `JWT_ALLOW_DEV_TOKEN` defaults to `false` in `jwt_auth.py` |

### CI Infrastructure (Complete)

| Item | Description | Implementation |
|------|-------------|----------------|
| **CI Preflight** | Consistency checks | `.github/workflows/ci-preflight.yml` |
| **Git Hooks** | Pre-commit/pre-push | `scripts/ops/setup_ci_hooks.sh` |
| **Consistency Checker** | 6-layer validation | `scripts/ops/ci_consistency_check.sh` |

---

## pgvector Integration Details

### Database Changes

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to memories table
ALTER TABLE memories ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_memories_embedding
  ON memories USING hnsw (embedding vector_cosine_ops);
```

### New File: `backend/app/memory/vector_store.py`

Features:
- **Semantic Search**: Cosine similarity with configurable threshold
- **Auto-Embedding**: OpenAI `text-embedding-3-small` (1536 dims)
- **HNSW Index**: Fast approximate nearest neighbor queries
- **Hybrid Search**: Falls back to keyword search when embeddings unavailable
- **Backfill Support**: `backfill_embeddings()` for existing memories

### Environment Variables

```bash
EMBEDDING_PROVIDER=openai        # or "anthropic" (requires VOYAGE_API_KEY)
OPENAI_API_KEY=sk-xxx            # Required for OpenAI embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

### Usage Example

```python
from app.memory.vector_store import get_vector_memory_store

store = get_vector_memory_store()

# Store with auto-embedding
memory_id = await store.store(
    agent_id="agent-123",
    text="Important information about the project",
)

# Semantic search
results = await store.search(
    agent_id="agent-123",
    query="project details",
    limit=5,
    similarity_threshold=0.5,
)
# Returns: [{"id": "...", "text": "...", "similarity": 0.87}, ...]
```

---

## Files Modified/Created

### Modified Files

| File | Changes |
|------|---------|
| `app/auth/rbac.py` | Added `RBAC_ENFORCE` flag and fail-closed behavior |
| `app/auth/clerk_provider.py` | Added fail-closed logic when `RBAC_ENFORCE=true` |
| `app/models/costsim_cb.py` | Added `CostSimCanaryReportModel` DB model |

### New Files

| File | Purpose |
|------|---------|
| `app/memory/vector_store.py` | pgvector-backed semantic memory store |

---

## Verification Results

### VectorMemoryStore Test

```
Stored memory: 8cdfbe2f-1fe2-4a68-8c61-5bce12786222
Retrieved: This is a test memory about pgvector integration...
Listed 2 memories
Keyword search found 2 results
Cleanup done

VectorMemoryStore working!
```

### pgvector Extension

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
-- oid | extname | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
-- 16392 | vector | 16389 | 2200 | t | 0.8.0 | |
```

---

## Already Implemented (Discovered)

During the stub sweep, we discovered these were already fully implemented:

1. **Redis Idempotency Store** - `idempotency.py` with atomic Lua scripts
2. **Provenance Async DB** - `provenance_async.py` with batch writes
3. **ClaudeAdapter** - Full Anthropic integration with error mapping
4. **S3ArtifactStore** - Pluggable storage for R2/S3/local

---

## Production Checklist

- [x] pgvector extension enabled in Neon
- [x] HNSW index created for fast similarity queries
- [x] VectorMemoryStore tested and working
- [x] Fallback to keyword search when embeddings unavailable
- [x] Environment variables documented
- [x] Set `OPENAI_API_KEY` in production for embeddings
- [x] Run `backfill_embeddings()` for existing memories (68/68 complete)

---

## Related PINs

- **PIN-045**: CI Infrastructure Fixes (same session)
- **PIN-038**: Upstash Redis Integration
- **PIN-034**: Vault Secrets Management
- **PIN-032**: M7 RBAC Enablement

---

## Embedding Backfill Results

**Completed:** 2025-12-07

```
Total Memories: 68
With Embeddings: 68
Pending: 0
Success Rate: 100%
```

### Critical Fix: asyncpg CAST Syntax

During backfill, discovered that asyncpg interprets `::` as named parameter syntax, causing SQL errors.

**Error:**
```
PostgresSyntaxError: syntax error at or near ":"
```

**Fix:** Changed all `::vector` casts to `CAST(:param AS vector)`:

```python
# WRONG - asyncpg interprets :: as parameter
embedding = :embedding::vector

# CORRECT - explicit CAST function
embedding = CAST(:embedding AS vector)
```

**Files Fixed:**
- `backend/app/memory/vector_store.py` (4 occurrences)
- `backend/scripts/backfill_memory_embeddings.py` (1 occurrence)

---

## P0 Security Hardening (2025-12-07)

### OpenAI Key Management

- **Vault Storage**: Added `OPENAI_API_KEY` to HashiCorp Vault at `agenticverz/external-apis`
- **Removed from .env**: Replaced plaintext key with reference comment
- **Secrets Directory**: Created `/root/agenticverz2.0/secrets/openai.env` (mode 600)

### Daily Quota Guard

Added embedding quota enforcement in `app/memory/embedding_metrics.py`:

```python
EMBEDDING_DAILY_QUOTA = int(os.getenv("EMBEDDING_DAILY_QUOTA", "10000"))

# Functions added:
check_embedding_quota()     # Returns False if quota exceeded
increment_embedding_count() # Track daily usage
get_embedding_quota_status() # Full status dict
```

- Resets at midnight UTC
- Blocks API calls when exceeded
- Prometheus metrics: `aos_embedding_quota_exhausted_total`, `aos_embedding_daily_calls`

### Prometheus Alerts

Created `monitoring/rules/embedding_alerts.yml` with critical alerts:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| `EmbeddingErrorRateHigh` | >5 errors in 5m | critical |
| `EmbeddingQuotaExceeded` | quota exhausted | critical |
| `EmbeddingQuotaNearLimit` | >80% used | warning |
| `EmbeddingLatencyHigh` | P95 >2s | warning |
| `BackfillStalled` | no progress 6h | critical |
| `VectorSearchFallbackHigh` | >50% fallback | warning |
| `VectorIndexIncomplete` | >100 null embeddings | warning |

---

## Next Steps

1. ~~Configure `OPENAI_API_KEY` for production embeddings~~ ✅ DONE
2. ~~Run embedding backfill for existing memories~~ ✅ DONE (68/68)
3. ~~Add daily quota guard~~ ✅ DONE
4. ~~Create Prometheus alerts~~ ✅ DONE
5. Monitor embedding generation costs
6. Consider Anthropic Voyage as alternative embedding provider
