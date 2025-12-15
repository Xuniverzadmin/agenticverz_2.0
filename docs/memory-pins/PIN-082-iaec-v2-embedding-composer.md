# PIN-082: IAEC v3.2 - Instruction-Aware Embedding Composer

**Date:** 2025-12-15
**Status:** COMPLETE
**Milestone:** M20 Prep / Memory Subsystem Enhancement
**Version:** 3.2.0

---

## Overview

IAEC (Instruction-Aware Embedding Composer) v3.2 implements a production-scale 4-slot embedding architecture with:
- **Reversible decomposition** for weighted mode embeddings
- **Temporal signatures** for model drift control
- **Deep embedding-based mismatch detection** with corrective actions
- **5-level policy encoding** (L0-L4) with softmax folding
- **Self-verifier** for slot integrity validation
- **Transform DAG Manager** for scalable version transforms
- **Correction cooldown** to prevent oscillation loops
- **Whitening versioning** declared in every output for audit replay

## v3.2 Additions (Production Scale Ready)

| Feature | Problem Solved | Implementation |
|---------|---------------|----------------|
| **Transform DAG Manager** | O(n²) transform matrices don't scale | Canonical paths, graph pruning, transitive collapsing |
| **Correction Cooldown** | Oscillation loops (A→B→A→B) poison routing | Window limit + monotonic correction policy |
| **Policy Softmax Folding** | Deep stacks distort weights | Softmax normalization ensures sum=1.0 |
| **Whitening Versioning** | Audit replay incomplete without basis info | `whitening_basis_id` + `whitening_version` in all outputs |

## v3.1 Additions (Production Critical)

| Feature | Problem Solved | Implementation |
|---------|---------------|----------------|
| **Temporal Mediation** | Mixing embeddings from different epochs poisons routing | `TemporalMediator` class with transformation matrices |
| **Corrective Action** | Detection without prescription | `CorrectiveAction` with confidence, alternatives, governance_rule |
| **5-Level Policy** | Flat policy encoding | L0-L4 hierarchy with `fold()` operator |
| **Whitening Persistence** | Recomputation breaks backward compat | Version-locked `.npz` storage |

## Problem Statement (v2.0)

Standard embedding approaches treat all queries uniformly, losing semantic context about the intended task:

1. **Instruction blindness** - "summarize X" and "extract from X" produce similar embeddings
2. **Context collapse** - Long context can dominate the embedding
3. **Non-verifiable composites** - No way to verify construction
4. **Cross-instruction drift** - Varying magnitudes across instructions

## v3.0 Additions

5. **No reversibility** - Cannot reconstruct slots from weighted embeddings
6. **No temporal tracking** - Drift between model versions undetected
7. **Naive mismatch detection** - Keyword-only fails on paraphrases
8. **No policy governance** - Missing organizational hierarchy encoding

---

## Architecture: 4-Slot (v3.0)

```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│INSTRUCTION│  QUERY   │ CONTEXT  │ TEMPORAL │  POLICY  │
│ (490 dim) │(490 dim) │(490 dim) │ (32 dim) │ (32 dim) │
├───────────┴──────────┴──────────┴──────────┴──────────┤
│           COMPOSITE EMBEDDING (1536 total)            │
└───────────────────────────────────────────────────────┘
```

### Slot Layout

| Slot | Start | End | Dimensions | Purpose |
|------|-------|-----|------------|---------|
| Instruction | 0 | 490 | 490 | Task type encoding |
| Query | 490 | 980 | 490 | User intent encoding |
| Context | 980 | 1470 | 490 | System context encoding |
| Temporal | 1472 | 1504 | 32 | Version/drift signature |
| Policy | 1504 | 1536 | 32 | Governance hierarchy |

---

## v3.0 Features

### 1. Reversible Decomposition

SlotBasis stores original vectors for weighted mode, enabling reconstruction:

```python
# Compose
result = await iaec.compose(instruction="summarize", query="...", mode="weighted")
print(result.slot_basis_hash)  # "f1a3ba2a8ca98559"

# Decompose
slots = iaec.decompose(result.vector, verify=True)
# Returns: instruction_slot, query_slot, context_slot, temporal_slot, policy_slot
```

### 2. Temporal Signature (32 dims)

Deterministic encoding for drift detection across model versions:

```python
temporal_signature = {
    "epoch_hash": "2025-12-15",
    "model_family": "openai",
    "model_version": "text-embedding-3-small",
    "iaec_version": "3.0.0",
    "slot_structure_version": 4
}
```

The temporal slot encodes this signature into 32 dimensions using deterministic hashing.

### 3. Deep Mismatch Detection

Embedding-based semantic compatibility (not just keywords):

```python
# v2.0: keyword-only
score = 1.0  # Triggers on keywords like "extract"

# v3.0: embedding-based
deep_score = 0.83  # Cosine similarity between instruction and query embeddings
detection_method = "embedding"  # More reliable than keywords
```

### 4. Policy Slot Encoding

Governance hierarchy in embedding space:

```python
# Request
{
    "policy_id": "pol_enterprise_001",
    "policy_version": 2,
    "policy_level": 1  # 0=global, 1=org, 2=team, 3=agent
}

# Response
policy_encoding = {
    "policy_id": "pol_enterprise_001",
    "policy_version": 2,
    "hierarchy_level": 1
}
```

### 5. Self-Verifier

Slot integrity validation:

```python
result = iaec.verify_integrity(embedding)
# Returns:
{
    "passed": True,
    "reconstruction_error": 0.0,
    "temporal_match": True,
    "policy_match": True,
    "slot_norms_valid": True
}
```

---

## API Endpoints

### POST /api/v1/embedding/compose

**Request (v3.0):**

```json
{
  "instruction": "summarize",
  "query": "What are the key points?",
  "context": "Document text...",
  "mode": "weighted",
  "policy_id": "pol_001",
  "policy_version": 2,
  "policy_level": 1
}
```

**Response (v3.0):**

```json
{
  "vector": [...],
  "mode": "weighted",
  "instruction": "summarize",
  "weights": [0.2, 0.5, 0.3],
  "dimensions": 1536,
  "query_hash": "76863934cbcb8c97",
  "instruction_hash": "944708af8935c5c0",
  "context_hash": "2fa459a46265a2b4",
  "provenance_hash": "3d6bae98fa372a8d050a7ecc8545cbeb",
  "mismatch_score": 0.83,
  "deep_mismatch_score": 0.81,
  "collapse_prevented": false,
  "values_clamped": false,
  "norm_coefficient": 1.0,
  "temporal_signature": {
    "epoch_hash": "2025-12-15",
    "model_family": "openai",
    "model_version": "text-embedding-3-small",
    "iaec_version": "3.0.0",
    "slot_structure_version": 4
  },
  "policy_id": "pol_001",
  "policy_encoding": {
    "policy_id": "pol_001",
    "policy_version": 2,
    "hierarchy_level": 1
  },
  "slot_basis_hash": "f1a3ba2a8ca98559",
  "integrity_verified": true,
  "reconstruction_error": 0.0,
  "created_at": "2025-12-15T16:02:27.081975+00:00",
  "iaec_version": "3.0.0"
}
```

### POST /api/v1/embedding/decompose

```json
// Request
{"vector": [...], "verify": true}

// Response
{
  "instruction_slot": [...],  // 490 dims
  "query_slot": [...],        // 490 dims
  "context_slot": [...],      // 490 dims
  "temporal_slot": [...],     // 32 dims
  "policy_slot": [...],       // 32 dims
  "is_valid": true,
  "reconstruction_error": 0.0,
  "temporal_compatible": true,
  "source_mode": "segmented"
}
```

### POST /api/v1/embedding/iaec/check-mismatch

```json
// Query params: ?instruction=summarize&query=extract%20all%20emails

// Response
{
  "instruction": "summarize",
  "query": "extract all email addresses",
  "score": 1.0,                    // Keyword-based
  "deep_score": 0.83,              // Embedding-based (v3.0)
  "suggested_instruction": "extract",
  "detection_method": "embedding",
  "message": "Embedding analysis suggests query is a 'extract' task..."
}
```

### GET /api/v1/embedding/iaec/segment-info

```json
{
  "iaec_version": "3.0.0",
  "embedding_dimensions": 1536,
  "content_dimensions": 1472,
  "segment_size": 490,
  "temporal_slot_size": 32,
  "policy_slot_size": 32,
  "slot_structure_version": 4,
  "slots": {
    "instruction": {"start": 0, "end": 490},
    "query": {"start": 490, "end": 980},
    "context": {"start": 980, "end": 1470},
    "temporal": {"start": 1472, "end": 1504},
    "policy": {"start": 1504, "end": 1536}
  },
  "temporal_signature": {...}
}
```

---

## Metrics (v3.0)

| Metric | Type | Labels |
|--------|------|--------|
| `aos_iaec_compositions_total` | Counter | instruction, mode, version |
| `aos_iaec_decompositions_total` | Counter | mode |
| `aos_iaec_integrity_checks_total` | Counter | passed |
| `aos_iaec_temporal_mismatches_total` | Counter | - |
| `aos_iaec_mismatch_warnings_total` | Counter | instruction, detection_method |
| `aos_iaec_collapse_events_total` | Counter | type |
| `aos_iaec_composition_latency_seconds` | Histogram | - |

---

## Files

| File | Purpose |
|------|---------|
| `backend/app/memory/iaec.py` | Core IAEC v3.0 module (~1456 lines) |
| `backend/app/api/embedding.py` | API endpoints with v3.0 models |

---

## Testing

```bash
# Compose with policy (v3.0)
curl -X POST /api/v1/embedding/compose \
  -H "X-AOS-Key: $AOS_API_KEY" \
  -d '{"instruction":"summarize","query":"key points","policy_id":"pol_001"}'

# Decompose
curl -X POST /api/v1/embedding/decompose \
  -H "X-AOS-Key: $AOS_API_KEY" \
  -d '{"vector":[...],"verify":true}'

# Check mismatch (deep detection)
curl -X POST "/api/v1/embedding/iaec/check-mismatch?instruction=summarize&query=extract%20emails" \
  -H "X-AOS-Key: $AOS_API_KEY"

# Segment info
curl -X GET /api/v1/embedding/iaec/segment-info \
  -H "X-AOS-Key: $AOS_API_KEY"
```

---

## Version History

| Version | Features |
|---------|----------|
| v2.0 | 3-slot architecture, anti-collapse, provenance tracking |
| v3.0 | 4-slot, reversibility, temporal signature, deep mismatch, policy encoding |
| v3.1 | Temporal mediation, 5-level policy (L0-L4), corrective action with confidence, whitening persistence |
| v3.2 | Transform DAG Manager, correction cooldown, softmax policy folding, whitening versioning in outputs |

---

## v3.2 New Features

### Transform DAG Manager

Prevents exponential complexity when managing multiple temporal signatures:

```python
mediator = TemporalMediator()

# Canonical path routing (avoids O(n²) transforms)
path = mediator._find_canonical_path(from_key, to_key)
# Returns: [from_key, canonical_key, to_key]

# Transitive collapsing (A→B→C becomes A→C)
mediator.collapse_transitive(from_key, via_key, to_key)

# Version pruning (keeps max N versions)
pruned = mediator.prune_old_versions(max_versions=10)

# DAG stats
stats = mediator.get_dag_stats()
```

### Correction Cooldown

Prevents oscillation loops where corrections ping-pong:

```python
from app.memory.iaec import get_correction_cooldown

cooldown = get_correction_cooldown()

# Check if correction is allowed
can_correct, reason = cooldown.can_correct("summarize", "extract")

# Record applied correction
cooldown.record_correction("summarize", "extract")

# Get cooldown state
state = cooldown.get_cooldown_state()
# Returns: recent_corrections, blocked_pairs, remaining_corrections
```

Configuration:
- `IAEC_CORRECTION_COOLDOWN`: Window in seconds (default: 60)
- `IAEC_CORRECTION_MAX_PER_WINDOW`: Max corrections per window (default: 3)

### Policy Softmax Folding

Ensures deep policy stacks don't distort weights:

```python
# v3.1: Simple weighted sum (can exceed bounds)
# v3.2: Softmax normalized weights (always sum to 1.0)
folded = PolicyEncoding.fold(policies, use_softmax=True)
```

### Whitening Versioning in Output

Every compose result now includes whitening metadata:

```json
{
  "whitening_basis_id": "wht_openai_f1a3ba2a8ca9",
  "whitening_version": "3.2.0/text-embedding-3-small/4"
}
```

---

## v3.1 New Classes

### TemporalMediator

Transforms embeddings from older versions to current slot basis:

```python
mediator = TemporalMediator()
mediator.set_current_signature(current_sig)

# Register transformation matrix
mediator.register_transform(old_sig, new_sig, transform_matrix)

# Transform old embedding
new_emb, was_mediated = mediator.mediate(old_embedding, old_sig)
```

### CorrectiveAction

Prescriptive mismatch resolution for M18/M19 governance:

```python
{
    "suggested_instruction": "extract",
    "confidence": 0.85,
    "should_auto_correct": true,
    "reason": "Query semantics match 'extract' better than 'summarize'",
    "alternatives": [("generate", 0.65), ("qa", 0.55)],
    "governance_rule": "M19/IAEC-SEMANTIC-ALIGNMENT"
}
```

### PolicyEncoding (5-Level)

Multi-level policy with folding:

```python
# Stack policies from all levels
policy = PolicyEncoding.from_stack(
    global_policy="pol_system_001",        # L0
    org_policy="pol_acme_corp",            # L1
    agent_class_policy="pol_summarizers",  # L2
    agent_instance_policy="pol_agent_42",  # L3
    task_policy="pol_urgent_task",         # L4
)

# Get folded vector (weighted by hierarchy)
folded_vec = policy.get_folded_vector()
```

### Whitening Persistence

Version-locked storage in `/tmp/iaec/`:

```
whitening_openai_text-embedding-3-small_3.1.0_4.npz
```

Contents:
- `matrix`: Whitening transformation matrix
- `mean`: Centering vector
- `iaec_version`: "3.1.0"
- `model_version`: "text-embedding-3-small"

---

## New Metrics (v3.1)

| Metric | Description |
|--------|-------------|
| `aos_iaec_temporal_mediations_total` | Cross-version embedding transformations |
| `aos_iaec_corrective_actions_total` | Prescriptive actions issued |
| `aos_iaec_policy_folding_total` | Multi-level policy folding operations |
| `aos_iaec_whitening_loads_total` | Whitening matrix disk loads |

---

## New Metrics (v3.2)

| Metric | Description |
|--------|-------------|
| `aos_iaec_dag_transforms_total` | Transform DAG operations (prune, collapse, canonical_path) |
| `aos_iaec_correction_cooldowns_total` | Correction cooldown events (window_limit, monotonic_block) |
| `aos_iaec_policy_softmax_total` | Policy folding with softmax normalization |

---

*PIN-082 updated 2025-12-15 (v3.2 production scale implementation complete)*
