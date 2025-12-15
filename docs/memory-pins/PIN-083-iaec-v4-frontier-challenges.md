# PIN-083: IAEC v4.0 Frontier Challenges

**Date:** 2025-12-15
**Status:** PLANNING
**Milestone:** M20 / MN-OS v1.0
**Dependency:** IAEC v3.2 (PIN-082)

---

## Overview

With IAEC v3.2 solving foundational issues (Transform DAG, oscillation prevention, softmax folding, whitening versioning), the next layer of engineering challenges emerges.

These are not flaws in v3.2 — they are the frontier problems only visible once the lower layers are solved.

---

## Challenge 1: Multi-Agent Slot Negotiation

### Problem

When multiple agents read/write embeddings into shared memory:

| Conflict Type | Description |
|---------------|-------------|
| Policy slot conflicts | Agent A's L4 policy vs Agent B's L4 policy |
| Temporal signature divergence | Agents initialized at different times |
| Corrective action confidence non-uniformity | Agent A trusts correction, Agent B doesn't |
| Transform chain inconsistency | Different agents have different transform paths |

### Scenario

```
Agent-A writes: summarize embedding with policy=pol_urgent
Agent-B reads: same memory, but has policy=pol_thorough
Agent-C queries: which policy slot wins?
```

### Required: Slot Arbitration Protocol

```python
class SlotArbitrator:
    def negotiate_policy(
        self,
        writer_policy: PolicyEncoding,
        reader_policy: PolicyEncoding,
        memory_policy: PolicyEncoding,
    ) -> PolicyEncoding:
        """
        Resolve policy conflict between writer, reader, and stored policy.

        Rules:
        - Higher hierarchy level wins (L4 > L3 > L2 > L1 > L0)
        - Same level: writer wins for writes, reader wins for reads
        - Memory policy is baseline
        """
        pass

    def negotiate_temporal(
        self,
        writer_sig: TemporalSignature,
        reader_sig: TemporalSignature,
        memory_sig: TemporalSignature,
    ) -> Tuple[TemporalSignature, bool]:
        """
        Resolve temporal signature conflicts.

        Returns:
            (canonical_sig, mediation_required)
        """
        pass
```

---

## Challenge 2: Distributed IAEC Coherency

### Problem

Running IAEC across multiple nodes (common in MN-OS) requires:

| Requirement | Risk if Violated |
|-------------|------------------|
| Identical whitening matrices | Vectors incompatible across nodes |
| Synchronized transform DAG | Mediation fails on cross-node vectors |
| Identical policy folding | Governance inconsistency |
| Shared correction cooldown | Oscillation across nodes |

### Required: Cluster-Wide State Sync Protocol

```python
class IAECClusterState:
    """
    Distributed IAEC state synchronization.

    Components to sync:
    - whitening_matrix: np.ndarray (immutable per version)
    - transform_dag: Dict[Tuple[str, str], np.ndarray]
    - policy_fold_weights: Dict[int, float]
    - correction_cooldown_state: CorrectionCooldown
    """

    def sync_whitening(self, node_id: str) -> bool:
        """Ensure whitening matrix matches cluster leader."""
        pass

    def sync_transform_dag(self, node_id: str) -> int:
        """Sync transform DAG, return number of transforms updated."""
        pass

    def broadcast_correction(self, original: str, suggested: str):
        """Broadcast correction to all nodes for cooldown sync."""
        pass

    def get_cluster_consensus(self) -> Dict[str, Any]:
        """Get consensus state across all nodes."""
        pass
```

### Sync Strategy Options

| Strategy | Pros | Cons |
|----------|------|------|
| Leader-based | Simple, consistent | Single point of failure |
| Gossip protocol | Resilient, scalable | Eventually consistent |
| Distributed lock | Strong consistency | Performance overhead |
| Version vectors | Conflict detection | Complex merge logic |

**Recommended:** Leader-based with gossip fallback.

---

## Challenge 3: Memory Sharding & Recomposition

### Problem

If storage layer shards IAEC vectors across nodes:

```
Node-1: dims 0-511     (instruction + partial query)
Node-2: dims 512-1023  (partial query + context)
Node-3: dims 1024-1535 (context + temporal + policy)
```

Reversible decomposition must still hold after recomposition.

### Required: Chunk-Aware Segmentation

```python
@dataclass
class ChunkedEmbedding:
    """Embedding with chunk metadata for sharded storage."""

    chunks: List[EmbeddingChunk]
    total_dimensions: int
    slot_boundaries: Dict[str, Tuple[int, int]]

    # Integrity tokens per chunk
    chunk_hashes: List[str]
    recomposition_token: str  # Hash of all chunk_hashes

    def validate_recomposition(self) -> bool:
        """Verify all chunks present and ordered correctly."""
        pass

    def reconstruct(self) -> np.ndarray:
        """Reconstruct full vector from chunks with validation."""
        pass

@dataclass
class EmbeddingChunk:
    chunk_id: str
    start_dim: int
    end_dim: int
    data: np.ndarray
    slot_overlap: List[str]  # Which slots this chunk contains
    integrity_hash: str
```

### Slot Integrity Tokens

```python
def generate_slot_integrity_token(
    vector: np.ndarray,
    slot_boundaries: Dict[str, Tuple[int, int]],
) -> str:
    """
    Generate integrity token that validates:
    - All slot boundaries present
    - Slot data not corrupted
    - Recomposition order correct
    """
    slot_hashes = []
    for slot_name, (start, end) in sorted(slot_boundaries.items()):
        slot_data = vector[start:end]
        slot_hash = hashlib.sha256(slot_data.tobytes()).hexdigest()[:8]
        slot_hashes.append(f"{slot_name}:{slot_hash}")

    return hashlib.sha256("|".join(slot_hashes).encode()).hexdigest()[:16]
```

---

## Challenge 4: Resource-Aware Composition (Cost-Safe IAEC)

### Problem

As vectors get more complex, IAEC needs cost governance:

| Situation | Current Behavior | Required Behavior |
|-----------|------------------|-------------------|
| High load | Full precision | Downshift to float16 |
| Low-stakes call | Full 4-slot | Reduced to 2-slot |
| Budget exhausted | Full composition | Fallback to weighted-only |
| Emergency | All features | Essential slots only |

### Required: Cost-Aware Composer

```python
class CostAwareIAEC:
    """
    IAEC with resource governance integration.

    Aligns with M19 Policy Layer and M20 cost governance.
    """

    def __init__(self, budget_controller: BudgetController):
        self.budget = budget_controller
        self.iaec = InstructionAwareEmbeddingComposer()

    async def compose_cost_aware(
        self,
        instruction: str,
        query: str,
        context: Optional[str] = None,
        importance: float = 1.0,  # 0.0 = low stakes, 1.0 = critical
        budget_remaining: float = 1.0,  # Fraction of budget left
    ) -> CompositeEmbedding:
        """
        Compose with cost-awareness.

        Rules:
        - importance < 0.3 AND budget < 0.5: Use weighted-only, skip policy
        - importance < 0.5 AND budget < 0.3: Use 2-slot (instruction + query)
        - budget < 0.1: Emergency mode - minimal embedding
        - Otherwise: Full composition
        """
        mode = self._select_mode(importance, budget_remaining)
        precision = self._select_precision(importance, budget_remaining)

        result = await self.iaec.compose(
            instruction=instruction,
            query=query,
            context=context if mode != "minimal" else None,
            mode=mode,
            store_basis=importance > 0.5,  # Only store basis for important calls
        )

        if precision == "float16":
            result.vector = result.vector.astype(np.float16)

        return result

    def _select_mode(self, importance: float, budget: float) -> str:
        if budget < 0.1:
            return "minimal"  # New mode: instruction + query only
        elif importance < 0.3 and budget < 0.5:
            return "weighted"  # Skip segmented overhead
        else:
            return "weighted"  # Default

    def _select_precision(self, importance: float, budget: float) -> str:
        if budget < 0.3 and importance < 0.7:
            return "float16"
        return "float32"
```

### Cost Metrics to Add

```python
IAEC_COST_DOWNSHIFTS = Counter(
    "aos_iaec_cost_downshifts_total",
    "Times IAEC reduced precision/complexity due to cost",
    ["reason"],  # budget_low, importance_low, emergency
)

IAEC_COMPOSITION_COST = Histogram(
    "aos_iaec_composition_cost_units",
    "Estimated cost units per composition",
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
)
```

---

## Implementation Priority

| Challenge | Priority | Blocking | Effort |
|-----------|----------|----------|--------|
| Multi-Agent Slot Negotiation | P1 | M20 multi-agent | Medium |
| Distributed Coherency | P1 | MN-OS scaling | High |
| Memory Sharding | P2 | Large-scale deployment | High |
| Cost-Aware Composition | P2 | M20 cost governance | Medium |

---

## Dependencies

- **IAEC v3.2** (PIN-082): Foundation must be stable
- **M19 Policy Layer** (PIN-078): Policy arbitration integration
- **M12 Multi-Agent** (PIN-062/063): Agent coordination
- **M20 Planning**: Overall MN-OS architecture

---

## Open Questions

1. **Slot Arbitration**: Should policy conflicts fail-safe (reject) or fail-forward (merge)?
2. **Distributed Sync**: What's the acceptable staleness for transform DAG?
3. **Sharding**: Should slots be atomic (never split) or splittable?
4. **Cost Governance**: Who decides importance score - agent, router, or policy layer?

---

*PIN-083 created 2025-12-15 (v4.0 planning document)*
